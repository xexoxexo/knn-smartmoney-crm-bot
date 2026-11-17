"""NLP chatbot CRM: normalisasi teks Indonesia, ekstraksi entitas (ID klien, target prediksi),
dan klasifikasi intent memakai TF-IDF + K-Nearest Neighbors (jarak cosine)."""
from __future__ import annotations

import json
import random
import re
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

import config

SLANG = {
    "gk": "tidak", "ga": "tidak", "gak": "tidak", "nggak": "tidak", "yg": "yang",
    "dgn": "dengan", "utk": "untuk", "tlg": "tolong", "bgt": "banget",
    "thx": "terima kasih", "makasih": "terima kasih", "trims": "terima kasih",
    "tq": "terima kasih", "thanks": "terima kasih", "hai": "halo", "hi": "halo",
    "hallo": "halo", "hey": "halo", "gimana": "bagaimana", "gmn": "bagaimana",
}
STOP = {"yang", "di", "ke", "dari", "itu", "ini", "kak", "min", "bot", "tolong", "mohon",
        "dong", "nih", "sih", "ya", "dengan", "untuk", "dan", "atau", "saya", "aku", "gue", "ada"}

# kata kunci -> target prediksi (urutan = prioritas; yang spesifik di depan)
TARGET_KEYWORDS = [
    ("high_budget_risk", ["risiko anggaran", "resiko anggaran", "budget risk", "risiko utang"]),
    ("has_emergency_fund", ["dana darurat", "emergency"]),
    ("high_profit_client", ["laba", "profit", "untung"]),
    ("high_invest_opportunity", ["peluang investasi", "proposal investasi"]),
    ("prefers_commodity_investment", ["komoditas", "emas", "bitcoin", "saham"]),
    ("high_monthly_spending", ["pengeluaran bulanan", "boros"]),
    ("cost_control_alert", ["kontrol biaya", "cost control", "biaya"]),
    ("high_salary_expense", ["gaji", "salary"]),
    ("on_budget", ["sesuai anggaran", "on budget", "anggaran"]),
]
_ID_RE = re.compile(r"\bc0*(\d{1,5})\b|\bklien\s+#?c?0*(\d{1,5})\b")


def normalize_client_id(token: str) -> str | None:
    m = re.fullmatch(r"\s*#?c?0*(\d{1,5})\s*", token.lower())
    return f"C{int(m.group(1)):04d}" if m else None


def preprocess(text: str) -> str:
    """lowercase -> ganti ID klien dengan token generik -> buang URL/tanda baca ->
    normalisasi slang -> buang stopword."""
    t = re.sub(r"https?://\S+", " ", text.lower())
    t = _ID_RE.sub(lambda m: " klien idklien " if m.group(0).startswith("klien") else " idklien ", t)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    out = []
    for tok in t.split():
        for w in SLANG.get(tok, tok).split():
            if w not in STOP:
                out.append(w)
    return " ".join(out)


@dataclass
class Entities:
    client_id: str | None = None
    target: str | None = None   # None = smart money (target utama)


def extract_entities(text: str) -> Entities:
    t = text.lower()
    ent = Entities()
    m = _ID_RE.search(t)
    if m:
        ent.client_id = f"C{int(m.group(1) or m.group(2)):04d}"
    if "smart money" not in t:
        for target, words in TARGET_KEYWORDS:
            if any(w in t for w in words):
                ent.target = target
                break
    return ent


def load_intents(path=config.INTENTS_PATH):
    data = json.loads(open(path, encoding="utf-8").read())["intents"]
    texts, labels, responses = [], [], {}
    for it in data:
        responses[it["tag"]] = it.get("responses", [])
        for p in it.get("patterns", []):
            texts.append(p)
            labels.append(it["tag"])
    return texts, labels, responses


@dataclass
class Prediction:
    intent: str
    confidence: float
    clean: str


class IntentClassifier:
    def __init__(self, texts, labels, k=3, threshold=0.35):
        self.k, self.threshold = k, threshold
        self.labels = np.array(labels)
        self.responses: dict = {}
        self.vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self.X = self.vec.fit_transform([preprocess(t) for t in texts])
        self.nn = NearestNeighbors(n_neighbors=min(k, len(texts)), metric="cosine", algorithm="brute").fit(self.X)

    @classmethod
    def from_file(cls, path=config.INTENTS_PATH, **kw):
        texts, labels, responses = load_intents(path)
        obj = cls(texts, labels, **kw)
        obj.responses = responses
        return obj

    def predict(self, text: str) -> Prediction:
        clean = preprocess(text)
        x = self.vec.transform([clean])
        if x.nnz == 0:  # tidak ada kata yang dikenal
            return Prediction("fallback", 0.0, clean)
        dist, idx = self.nn.kneighbors(x)
        sims = 1.0 - dist[0]
        votes = defaultdict(float)
        for s, i in zip(sims, idx[0]):
            votes[self.labels[i]] += s
        intent, score = max(votes.items(), key=lambda kv: kv[1])
        # confidence = kesepakatan tetangga x kemiripan tetangga terdekat
        conf = float(score / max(sum(votes.values()), 1e-9) * sims.max())
        if conf < self.threshold:
            return Prediction("fallback", conf, clean)
        return Prediction(str(intent), conf, clean)

    def reply(self, intent: str, name: str = "") -> str:
        options = self.responses.get(intent) or self.responses.get("fallback") or ["..."]
        return random.choice(options).replace("{nama}", name)


def evaluate_loo(k=3, threshold=0.35) -> float:
    """Leave-one-out accuracy untuk intent classifier (fallback dihitung salah)."""
    texts, labels, _ = load_intents()
    hits = 0
    for i in range(len(texts)):
        clf = IntentClassifier(texts[:i] + texts[i + 1:], labels[:i] + labels[i + 1:], k, threshold)
        hits += clf.predict(texts[i]).intent == labels[i]
    return hits / len(texts)
