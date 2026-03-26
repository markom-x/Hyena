import os
import re
import time
import logging
from urllib.parse import urlparse

import redis
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options


# =========================
# CONFIG
# =========================
GROUP_NAME = os.getenv("GROUP_NAME", "DIARIO DI BORDO")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_STREAM = os.getenv("REDIS_STREAM", "whatsapp")
PROFILE_DIR = os.getenv("MASTER_PROFILE_DIR", "/home/azureuser/chrome-profiles/master")
CHECK_INTERVAL = 2

QR_REGEX = r"https?://qr\.unipi\.it/[^\s]+"


# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# =========================
# REDIS
# =========================
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


# =========================
# SELENIUM SETUP
# =========================
def create_driver(profile_dir: str):
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1400,1000")

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def create_opener_driver():
    chrome_options = Options()
    chrome_options.add_argument("--user-data-dir=/home/azureuser/chrome-profiles/master-opener")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1200,900")

    driver = webdriver.Chrome(options=chrome_options)
    return driver


# =========================
# WHATSAPP HELPERS
# =========================
def wait_for_login(driver, timeout=60):
    logging.info("Apro WhatsApp Web…")
    driver.get("https://web.whatsapp.com")

    start = time.time()
    while time.time() - start < timeout:
        try:
            # Se il box di ricerca è visibile, il login è andato
            driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
            logging.info("Login WhatsApp OK (QR non visibile).")
            return True
        except:
            time.sleep(2)

    raise TimeoutError("Login WhatsApp non completato entro il timeout.")


def open_group(driver, group_name: str):
    search_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
    search_box.click()
    time.sleep(1)
    search_box.send_keys(Keys.CONTROL, "a")
    search_box.send_keys(Keys.BACKSPACE)
    search_box.send_keys(group_name)
    logging.info(f"Inviato nome gruppo: {group_name}")
    time.sleep(3)

    group = driver.find_element(By.XPATH, f'//span[@title="{group_name}"]')
    group.click()
    logging.info(f"Gruppo aperto: {group_name}")
    time.sleep(2)


def extract_links_from_page(driver):
    messages = driver.find_elements(By.XPATH, '//span[contains(@class, "selectable-text")]')
    found_links = []

    for msg in messages[-20:]:  # solo ultimi messaggi
        text = msg.text.strip()
        matches = re.findall(QR_REGEX, text)
        found_links.extend(matches)

    return found_links


# =========================
# MAIN
# =========================
def main():
    driver = create_driver(PROFILE_DIR)
    logging.info("Driver WhatsApp avviato.")

    opener_driver = None
    seen_links = set()

    try:
        wait_for_login(driver)
        open_group(driver, GROUP_NAME)

        opener_driver = create_opener_driver()
        logging.info("Driver opener avviato (profilo separato).")
        logging.info(f"Monitorando il gruppo: {GROUP_NAME} (IN e OUT)")

        while True:
            links = extract_links_from_page(driver)

            for link in links:
                if link not in seen_links:
                    seen_links.add(link)

                    # Apri sul browser master
                    try:
                        opener_driver.get(link)
                        logging.info(f"[MASTER] Aperto URL: {link}")
                    except Exception as e:
                        logging.error(f"[MASTER] Errore apertura URL: {e}")

                    # Pubblica su Redis stream
                    try:
                        r.xadd(REDIS_STREAM, {"url": link})
                        logging.info(f"[REDIS] Pubblicato su stream:{REDIS_STREAM}: {link}")
                    except Exception as e:
                        logging.error(f"[REDIS] Errore pubblicazione stream: {e}")

            time.sleep(CHECK_INTERVAL)

    except Exception as e:
        logging.exception(f"Errore fatale nel master: {e}")
        raise

    finally:
        if opener_driver:
            opener_driver.quit()
        driver.quit()


if __name__ == "__main__":
    main()
