"""Lapisan CRM (SQLAlchemy): data keuangan klien, pelanggan Telegram, log interaksi,
log prediksi, dan segmentasi. Default SQLite; ganti DATABASE_URL untuk PostgreSQL/MySQL."""
from datetime import datetime, timezone

from sqlalchemy import (BigInteger, Column, Float, Integer, MetaData, String, Table, Text,
                        create_engine, func, insert, select, update)

import config
import crm_data

engine = create_engine(config.DATABASE_URL, future=True)
metadata = MetaData()

clients = Table("clients", metadata,
                Column("client_id", String(20), primary_key=True),
                *[Column(c, Float) for c in crm_data.RAW_COLS])
customers = Table("customers", metadata,
                  Column("user_id", BigInteger, primary_key=True, autoincrement=False),
                  Column("username", String(64)), Column("first_name", String(128)),
                  Column("created_at", String(32)), Column("last_seen", String(32)),
                  Column("interaction_count", Integer, default=0),
                  Column("segment", String(16), default="baru"))
interactions = Table("interactions", metadata,
                     Column("id", Integer, primary_key=True, autoincrement=True),
                     Column("user_id", BigInteger), Column("text", Text), Column("intent", String(32)),
                     Column("confidence", Float), Column("created_at", String(32)))
predictions = Table("predictions", metadata,
                    Column("id", Integer, primary_key=True, autoincrement=True),
                    Column("user_id", BigInteger), Column("client_id", String(20)),
                    Column("target", String(40)), Column("label", Integer), Column("prob", Float),
                    Column("k", Integer), Column("created_at", String(32)))


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db():
    metadata.create_all(engine)


def segment_for(n: int) -> str:
    return "loyal" if n >= 20 else "aktif" if n >= 5 else "baru"


# ------------------------------------------------------------ data klien (CRM)
def seed_if_empty() -> int:
    """Isi tabel clients dari dataset (sintetis atau CSV) bila masih kosong."""
    with engine.begin() as c:
        if c.execute(select(func.count()).select_from(clients)).scalar():
            return 0
        df = crm_data.load_dataset()[["client_id"] + crm_data.RAW_COLS]
        c.execute(insert(clients), df.to_dict("records"))
        return len(df)


def get_client(client_id: str) -> dict | None:
    with engine.connect() as c:
        row = c.execute(select(clients).where(clients.c.client_id == client_id)).mappings().first()
    return dict(row) if row else None


def sample_client_ids(n: int = 3) -> list[str]:
    with engine.connect() as c:
        return [r[0] for r in c.execute(select(clients.c.client_id).order_by(func.random()).limit(n))]


# ----------------------------------------------------- pelanggan Telegram (CRM)
def upsert_customer(user_id, username, first_name):
    now = _now()
    with engine.begin() as c:
        exists = c.execute(select(customers.c.user_id).where(customers.c.user_id == user_id)).first()
        if exists:
            c.execute(update(customers).where(customers.c.user_id == user_id)
                      .values(username=username, first_name=first_name, last_seen=now))
        else:
            c.execute(insert(customers).values(user_id=user_id, username=username, first_name=first_name,
                                               created_at=now, last_seen=now, interaction_count=0, segment="baru"))


def log_interaction(user_id, text, intent, confidence):
    with engine.begin() as c:
        c.execute(insert(interactions).values(user_id=user_id, text=text, intent=intent,
                                              confidence=float(confidence), created_at=_now()))
        n = (c.execute(select(customers.c.interaction_count).where(customers.c.user_id == user_id)).scalar() or 0) + 1
        c.execute(update(customers).where(customers.c.user_id == user_id)
                  .values(interaction_count=n, segment=segment_for(n)))


def log_prediction(user_id, client_id, target, label, prob, k):
    with engine.begin() as c:
        c.execute(insert(predictions).values(user_id=user_id, client_id=client_id, target=target,
                                             label=int(label), prob=float(prob), k=int(k), created_at=_now()))


def recent_predictions(user_id, limit=5) -> list[dict]:
    with engine.connect() as c:
        rows = c.execute(select(predictions).where(predictions.c.user_id == user_id)
                         .order_by(predictions.c.id.desc()).limit(limit)).mappings().all()
    return [dict(r) for r in rows]


def stats() -> dict:
    with engine.connect() as c:
        count = lambda t: c.execute(select(func.count()).select_from(t)).scalar()
        group = lambda col, tbl, n=None: {
            str(k): v for k, v in c.execute(
                select(col, func.count()).select_from(tbl).group_by(col).order_by(func.count().desc()).limit(n))}
        return {"klien": count(clients), "pelanggan": count(customers), "interaksi": count(interactions),
                "prediksi": count(predictions), "segmen": group(customers.c.segment, customers),
                "intent": group(interactions.c.intent, interactions, 5),
                "label": group(predictions.c.label, predictions)}
