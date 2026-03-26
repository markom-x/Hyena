import os
import time
import argparse
import logging

import redis
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# =========================
# ARGUMENTS
# =========================
parser = argparse.ArgumentParser()
parser.add_argument("--profile", required=True, help="Percorso profilo Chrome del worker")
parser.add_argument("--consumer", required=True, help="Nome consumer Redis")
parser.add_argument("--group", default="workers", help="Nome consumer group Redis")
args = parser.parse_args()


# =========================
# CONFIG
# =========================
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_STREAM = os.getenv("REDIS_STREAM", "whatsapp")
BLOCK_MS = 5000


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
# SELENIUM
# =========================
def create_driver(profile_dir: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def ensure_group():
    try:
        r.xgroup_create(REDIS_STREAM, args.group, id="$", mkstream=True)
        logging.info(f"Creato consumer group '{args.group}' sullo stream '{REDIS_STREAM}'")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            pass
        else:
            raise


def main():
    ensure_group()
    driver = create_driver(args.profile)

    logging.info(f"[{args.consumer}] in ascolto su stream:{REDIS_STREAM}...")

    try:
        while True:
            messages = r.xreadgroup(
                groupname=args.group,
                consumername=args.consumer,
                streams={REDIS_STREAM: ">"},
                count=1,
                block=BLOCK_MS
            )

            if not messages:
                continue

            for stream_name, entries in messages:
                for entry_id, data in entries:
                    url = data.get("url")
                    if not url:
                        r.xack(REDIS_STREAM, args.group, entry_id)
                        continue

                    try:
                        logging.info(f"[{args.consumer}] apro: {url}")
                        driver.get(url)
                        time.sleep(3)  # tempo minimo per far caricare la pagina
                    except Exception as e:
                        logging.error(f"[{args.consumer}] errore apertura: {e}")
                    finally:
                        r.xack(REDIS_STREAM, args.group, entry_id)

    except Exception as e:
        logging.exception(f"[{args.consumer}] errore fatale: {e}")
        raise

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
