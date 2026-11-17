"""Konfigurasi terpusat (dibaca dari file .env)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR / "models"
REPORT_DIR = BASE_DIR / "reports"
MODEL_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

INTENTS_PATH = BASE_DIR / "data" / "intents.json"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'crm.db'}")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

DATA_SOURCE = os.getenv("DATA_SOURCE", "synthetic")  # synthetic | csv
CSV_PATH = Path(os.getenv("CSV_PATH", str(BASE_DIR / "data" / "clients.csv")))
N_CLIENTS = int(os.getenv("N_CLIENTS", "1500"))
LABEL_NOISE = float(os.getenv("LABEL_NOISE", "0.05"))

CV_FOLDS = int(os.getenv("CV_FOLDS", "5"))        # naskah: k-fold CV (k = 5 atau 10)
RANDOM_STATE = int(os.getenv("RANDOM_STATE", "42"))
