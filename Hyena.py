import os
import time
import logging
import sys
import base64
import webbrowser
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from PIL import Image
from pyzbar.pyzbar import decode
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    NoSuchElementException,
)
from selenium.webdriver.common.action_chains import ActionChains

# -------------- IMPORT PER CHROME --------------
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions

# -----------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("whatsapp_automation.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger()


# Funzione per verificare se una stringa è un URL valido
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


# ======================
# 1) WebDriver per Edge
# ======================
edge_options = Options()
edge_options.use_chromium = True

# Specifica il percorso del profilo utente (quello dove hai WhatsApp Web loggato)
edge_options.add_argument(r"--user-data-dir=C:\Edge_User_Data")
edge_options.add_argument(r"--profile-directory=Default")  # Modifica se necessario

service = webdriver.edge.service.Service(EdgeChromiumDriverManager().install())

try:
    driver = webdriver.Edge(service=service, options=edge_options)
    logger.info("WebDriver Edge avviato con successo con WebDriver Manager (profilo Edge).")
except Exception as e:
    logger.error(f"Errore nell'avvio del WebDriver Edge: {e}")
    sys.exit(1)

logger.info(f"Directory corrente: {os.getcwd()}")

# ======================================
# 2) WebDriver per Chrome (secondo profilo)
# ======================================
chrome_options = ChromeOptions()

# Se desideri usare un profilo specifico di Chrome (diverso dall'utente di default),
# puoi abilitare queste linee (e crearti una cartella dedicata se serve).
chrome_options.add_argument(r"--user-data-dir=C:\Chrome_User_Data_2")
chrome_options.add_argument(r"--profile-directory=Profile_2")

chrome_service = ChromeService(ChromeDriverManager().install())

try:
    driver_chrome = webdriver.Chrome(service=chrome_service, options=chrome_options)
    logger.info("Secondo WebDriver Chrome avviato con successo (profilo Chrome).")
except Exception as e:
    logger.error(f"Errore nell'avvio del WebDriver Chrome: {e}")
    sys.exit(1)

# ====================
# Accesso WhatsApp Web
# ====================
driver.get('https://web.whatsapp.com')
logger.info("Verificando lo stato di accesso a WhatsApp Web...")
time.sleep(5)

# Controlla se è necessario effettuare il login per Edge
try:
    qr_code = driver.find_element(By.XPATH, '//canvas[@aria-label="Scan me!"]')
    logger.info("Devi scannerizzare il QR code su Edge per accedere a WhatsApp Web.")
    time.sleep(15)  # Tempo per scannerizzare il QR code
except NoSuchElementException:
    logger.info("Sei già loggato su WhatsApp Web nel profilo Edge.")


# Specifica il nome del gruppo da monitorare
group_name = "II anno A-K"  # Sostituisci con il nome esatto del tuo gruppo


def open_group(name):
    try:
        # Attendi un po' di più se necessario, per assicurare che la pagina sia caricata
        time.sleep(20)
        search_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
        search_box.click()
        search_box.clear()
        search_box.send_keys(name)
        logger.info(f"Inviato il nome del gruppo: {name}")
        time.sleep(2)
        group = driver.find_element(By.XPATH, f'//span[@title="MEDICINA AK"]')
        group.click()
        scroll_button_xpath = "//div[@role='button' and @aria-label='Scorri in fondo']"
        scroll_button = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, scroll_button_xpath))
        )
        if scroll_button.is_displayed():
            scroll_button.click()
            print("Pulsante 'Scorri in fondo' trovato e cliccato.")
    except Exception as e:
        logger.error(f"Errore nell'aprire il gruppo: {e}")


def download_image(img_element, download_path='downloads'):
    download_path = os.path.join(download_path, 'QR scans')
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    logger.info("Estraendo i dati dell'immagine...")

    try:
        # Utilizza JavaScript per ottenere i dati base64 dell'immagine
        base64_str = driver.execute_script("""
            var img = arguments[0];
            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png').substring(22);
        """, img_element)

        if not base64_str:
            logger.error("Impossibile estrarre i dati dell'immagine.")
            return None

        # Decodifica i dati base64 e salva l'immagine
        img_data = base64.b64decode(base64_str)
        img_cropped_path = os.path.join(download_path, f"cropped_{int(time.time())}.png")
        with open(img_cropped_path, 'wb') as f:
            f.write(img_data)
        logger.info(f"Immagine salvata come: {img_cropped_path}")
        return img_cropped_path
    except Exception as e:
        logger.error(f"Errore durante il download dell'immagine: {e}")
        return None


def decode_qr(image_path):
    try:
        img = Image.open(image_path)
        decoded_objects = decode(img)
        for obj in decoded_objects:
            return obj.data.decode('utf-8')
        return None
    except Exception as e:
        logger.error(f"Errore durante la decodifica del QR code: {e}")
        return None


def main():
    open_group(group_name)
    logger.info(f"Monitorando il gruppo: {group_name}")
    opened_urls = set()  # Traccia gli URL già aperti

    while True:
        try:
            # Trova tutti i messaggi nel gruppo
            messages = driver.find_elements(By.XPATH, '//div[contains(@class, "message-in")]')

            # Analizza sempre l'ultimo messaggio inviato nel gruppo
            if messages:
                message = messages[-1]  # Seleziona sempre l'ultimo messaggio
                logger.info("Elaborando l'ultimo messaggio.")
                try:
                    # Puoi stampare il testo del messaggio per verifica
                    try:
                        message_text = message.find_element(By.XPATH,
                                                            './/span[contains(@class, "selectable-text")]').text
                        logger.info(f"Testo del messaggio: {message_text}")
                    except NoSuchElementException:
                        logger.info("Messaggio senza testo.")

                    # Trova tutte le immagini nel messaggio e processa l'ultima
                    images = message.find_elements(By.XPATH, './/img[contains(@src, "blob:")]')
                    logger.info(f"Trovate {len(images)} immagini nel messaggio.")
                    if images:
                        # Seleziona l'ultima immagine (quella più recente)
                        img = images[-1]
                        logger.info(f"Selezionata l'ultima immagine con src: {img.get_attribute('src')}")
                        img_path = download_image(img)
                        time.sleep(1)
                        if img_path:
                            logger.info(f"Immagine scaricata: {img_path}")
                            qr_data = decode_qr(img_path)
                            if qr_data:
                                logger.info(f"QR Code Decodificato: {qr_data}")
                                if is_valid_url(qr_data):
                                    if qr_data not in opened_urls:
                                        logger.info(f"Apro l'URL decodificato: {qr_data}")

                                        # 1) Se vuoi aprirlo col browser di sistema:
                                        webbrowser.open(qr_data)

                                        # 2) Apri lo stesso URL in Chrome (secondo browser)
                                        driver_chrome.get(qr_data)

                                        opened_urls.add(qr_data)
                                    else:
                                        logger.info(f"L'URL {qr_data} è già stato aperto.")
                                else:
                                    logger.info("Il QR code non contiene un URL valido.")
                            else:
                                logger.info("Nessun QR code trovato nell'immagine.")
                        else:
                            logger.info("Immagine non scaricata.")
                    else:
                        logger.info("Nessuna immagine trovata nel messaggio. Controllo il testo per URL QR.")
                        if message_text.startswith("https://qr.unipi.it"):
                            logger.info(f"Trovato URL unipi: {message_text}")
                            if message_text not in opened_urls:
                                logger.info(f"Apro l'URL: {message_text}")

                                # 1) Browser di sistema
                                webbrowser.open(message_text)

                                # 2) Chrome
                                driver_chrome.get(message_text)

                                opened_urls.add(message_text)
                            else:
                                logger.info(f"L'URL {message_text} è già stato aperto.")
                except StaleElementReferenceException as e:
                    logger.error(f"Errore durante l'elaborazione del messaggio: {e}")
                except Exception as e:
                    logger.error(f"Errore durante l'elaborazione del messaggio: {e}")
        except Exception as e:
            logger.error(f"Errore nel ciclo principale: {e}")

        time.sleep(1)  # Attendi 1 secondo prima del prossimo controllo


if __name__ == "__main__":
    main()
