"""Bot Telegram CRM: memprediksi pola smart money klien dengan KNN.

Jalankan:  python bot.py
"""
from __future__ import annotations

import asyncio
import html
import json
import logging

import pandas as pd
from telegram import Update, User
from telegram.constants import ChatAction, ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import config
import crm
import crm_data
import model
from nlp import IntentClassifier, extract_entities, normalize_client_id

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
log = logging.getLogger("bot")

NLP = IntentClassifier.from_file()
BUNDLES: dict = {}  # target -> model KNN, diisi saat startup
HELP = ("<b>Perintah</b>\n/klien izaki - prediksi smart money &amp; indikator keuangan klien\n"
        "/prediksi key=value ... - prediksi dari data baru\n/fitur - pemetaan fitur CRM (Tabel 5)\n"
        "/riwayat - 5 prediksi terakhir\n/analisis - hasil evaluasi algoritma KNN\n/stats - statistik CRM\n\n"
        "Atau tanya bebas: <i>apakah klien 12 smart money?</i>")


def touch(update: Update):
    u = update.effective_user
    crm.upsert_customer(u.id, u.username, u.first_name)
    return u


def rp(x) -> str:  # juta Rupiah, format Indonesia
    return f"{x:,.0f}".replace(",", ".")


def yn(label: int) -> str:
    return "YA" if label else "TIDAK"


def format_card(title: str, raw: dict, preds: dict, only: str | None = None) -> str:
    feats = crm_data.engineer_features(pd.DataFrame([{c: raw.get(c) for c in crm_data.RAW_COLS}])).iloc[0]
    if only:
        p = preds[only]
        return (f"👤 <b>{html.escape(title)}</b>\n{crm_data.TARGETS[only]}: <b>{yn(p['label'])}</b> ({p['prob']:.0%})\n"
                f"Klien serupa: " + ", ".join(f"{s['client_id']} ({yn(s['label']).lower()})" for s in p["similar"]))
    sm = preds["smart_money"]
    lines = [f"👤 <b>{html.escape(title)}</b>",
             f"{'🟢' if sm['label'] else '🔴'} Smart money: <b>{yn(sm['label'])}</b> ({sm['prob']:.0%}) · K={sm['k']}",
             "Klien serupa: " + ", ".join(f"{s['client_id']} ({yn(s['label']).lower()})" for s in sm["similar"]),
             "", "<b>Profil keuangan</b> (juta Rp)"]
    if pd.notna(raw.get("total_revenue")):
        lines.append(f"• Pendapatan {rp(raw['total_revenue'])}" +
                     (f" · laba {rp(raw['total_profit'])}" if pd.notna(raw.get("total_profit")) else ""))
    shown = [("profit_margin", "Margin laba", "{:.0%}"), ("emergency_fund_ratio", "Dana darurat / pendapatan", "{:.0%}"),
             ("cost_income_ratio", "Rasio biaya", "{:.0%}"), ("budget_utilization", "Realisasi anggaran", "{:.0%}")]
    lines += [f"• {n}: {f.format(feats[c])}" for c, n, f in shown if pd.notna(feats[c])]
    lines += ["", "<b>Indikator Tabel 5</b>"]
    for t in crm_data.TARGET_ORDER[1:]:
        p = preds[t]
        warn = "⚠️ " if (t in crm_data.NEGATIVE_TARGETS and p["label"]) else ""
        lines.append(f"• {warn}{crm_data.TARGETS[t]}: {yn(p['label']).lower()} ({p['prob']:.0%})")
    lines += ["", "⚠️ <i>Keluaran model statistik sebagai pendukung keputusan, bukan saran investasi.</i>"]
    return "\n".join(lines)


async def run_client(update: Update, client_id: str, only: str | None = None):
    msg = update.effective_message
    await update.effective_chat.send_action(ChatAction.TYPING)
    raw = crm.get_client(client_id)
    if raw is None:
        ex = ", ".join(crm.sample_client_ids(3))
        await msg.reply_text(f"Klien {html.escape(client_id)} tidak ditemukan. Contoh ID: {ex}")
        return
    preds = await asyncio.to_thread(model.predict_client, BUNDLES, raw, client_id)
    p = preds[only or "smart_money"]
    crm.log_prediction(update.effective_user.id, client_id, only or "smart_money", p["label"], p["prob"], p["k"])
    await msg.reply_text(format_card(f"Klien {client_id}", raw, preds, only), parse_mode=ParseMode.HTML)


# ---------------------------------------------------------------- commands
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = touch(update)
    await update.effective_message.reply_text(
        f"Halo {html.escape(u.first_name or '')}! 👋 Aku chatbot CRM untuk memprediksi pola "
        f"<b>smart money</b> (pengelolaan dana cerdas) klien dengan KNN.\n\n{HELP}", parse_mode=ParseMode.HTML)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch(update)
    await update.effective_message.reply_text(HELP, parse_mode=ParseMode.HTML)


async def klien_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch(update)
    cid = normalize_client_id(context.args[0]) if context.args else None
    if not cid:
        await update.effective_message.reply_text("Format: /klien izaki (atau /klien 12)")
        return
    await run_client(update, cid)


async def prediksi_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch(update)
    raw, bad = {}, []
    for a in context.args:
        k, _, v = a.partition("=")
        try:
            if k not in crm_data.RAW_COLS:
                raise KeyError
            raw[k] = float(v.replace(",", "."))
        except (KeyError, ValueError):
            bad.append(a)
    if len(raw) < 4 or bad:
        note = f"Tidak dikenali: {html.escape(', '.join(bad))}\n" if bad else ""
        await update.effective_message.reply_text(
            f"{note}Isi minimal 4 kolom, contoh:\n<code>/prediksi total_revenue=5000 total_profit=1400 "
            f"emergency_fund_balance=600 annual_expenses=3200 annual_budget=3500</code>\nDaftar kolom: /fitur",
            parse_mode=ParseMode.HTML)
        return
    preds = await asyncio.to_thread(model.predict_client, BUNDLES, raw)
    sm = preds["smart_money"]
    crm.log_prediction(update.effective_user.id, "manual", "smart_money", sm["label"], sm["prob"], sm["k"])
    await update.effective_message.reply_text(format_card("Data manual", raw, preds), parse_mode=ParseMode.HTML)


async def fitur_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch(update)
    lines = ["<b>Pemetaan fitur CRM → target</b> (Tabel 5)"]
    lines += [f"• <b>{f}</b>: <code>{html.escape(c)}</code> → {crm_data.TARGETS[t]}" for f, c, _, t in crm_data.TABLE5]
    lines += ["", "Target utama: <b>smart money</b> = minimal 6 dari 7 indikator sehat terpenuhi.",
              "Satuan uang: juta Rupiah per tahun."]
    await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def riwayat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = touch(update)
    rows = crm.recent_predictions(u.id)
    if not rows:
        await update.effective_message.reply_text("Belum ada riwayat. Coba /klien izaki")
        return
    lines = ["<b>5 prediksi terakhirmu</b>"] + [
        f"• {r['created_at'][:16].replace('T', ' ')} · {r['client_id']} → "
        f"{crm_data.TARGETS.get(r['target'], r['target'])}: {yn(r['label']).lower()} ({r['prob']:.0%})" for r in rows]
    await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def analisis_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch(update)
    path = config.REPORT_DIR / "metrics.json"
    if not path.exists():
        await update.effective_message.reply_text("Laporan belum ada. Jalankan <code>python analysis.py</code> dulu.", parse_mode=ParseMode.HTML)
        return
    m = json.loads(path.read_text())
    bp, t = m["best_params"], m["test"]
    comp = "\n".join(f"• {r['model']}: F1 {r['f1']:.2f} · AUC {r['roc_auc']:.2f} · akurasi {r['accuracy']:.0%}" for r in m["comparison"])
    text = (f"🧪 <b>Evaluasi KNN — target smart money</b>\n"
            f"Data: {m['data_source']} ({m['n_clients']} klien) · CV {m['cv_folds']}-fold · {m['grid_configs']} konfigurasi\n"
            f"Terbaik: K={bp['k']}, jarak {bp['metric']}, bobot {bp['weights']}, skala {bp['scaler']}, "
            f"SMOTE {'ya' if bp['smote'] else 'tidak'}\n"
            f"CV F1 {m['cv']['f1']:.2f} · AUC {m['cv']['roc_auc']:.2f}\n"
            f"Uji: akurasi {t['accuracy']:.0%} · presisi {t['precision']:.2f} · recall {t['recall']:.2f} · "
            f"F1 {t['f1']:.2f} · AUC {t['roc_auc']:.2f}\n"
            f"Akurasi tebak kelas mayoritas: {m['majority_accuracy']:.0%}\n\n<b>Perbandingan model (data uji)</b>\n{comp}\n\n"
            f"Akurasi intent NLP (LOO): {m['nlp_intent_loo_accuracy']:.0%}")
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)
    for name in ("k_vs_f1.png", "roc_curve.png", "confusion_matrix.png"):
        img = config.REPORT_DIR / name
        if img.exists():
            with open(img, "rb") as fh:
                await update.effective_message.reply_photo(fh)


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch(update)
    s = crm.stats()
    fmt = lambda d: ", ".join(f"{k}: {v}" for k, v in d.items()) or "-"
    await update.effective_message.reply_text(
        f"📈 <b>Statistik CRM</b>\nKlien: {s['klien']} · Pelanggan bot: {s['pelanggan']} ({fmt(s['segmen'])})\n"
        f"Interaksi: {s['interaksi']} · Prediksi: {s['prediksi']}\nIntent teratas: {fmt(s['intent'])}",
        parse_mode=ParseMode.HTML)


# ------------------------------------------------------------ free text NLP
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message or not update.effective_message.text:
        return
    u = touch(update)
    text = update.effective_message.text
    pred = NLP.predict(text)
    crm.log_interaction(u.id, text, pred.intent, pred.confidence)
    log.info("intent=%s conf=%.2f clean=%r", pred.intent, pred.confidence, pred.clean)
    msg = update.effective_message

    if pred.intent == "prediksi_klien":
        ent = extract_entities(text)
        if ent.client_id:
            await run_client(update, ent.client_id, ent.target)
        else:
            await msg.reply_text("Sebutkan ID kliennya, mis. \"cek klien izaki\".")
    elif pred.intent == "riwayat":
        await riwayat_cmd(update, context)
    elif pred.intent == "evaluasi_model":
        await analisis_cmd(update, context)
    elif pred.intent == "fitur_data":
        await fitur_cmd(update, context)
    elif pred.intent == "bantuan":
        await help_cmd(update, context)
    else:
        await msg.reply_text(NLP.reply(pred.intent, html.escape(u.first_name or "")))


def main():
    global BUNDLES
    if not config.BOT_TOKEN:
        raise SystemExit("Isi TELEGRAM_BOT_TOKEN di file .env (salin dari .env.example)")
    crm.init_db()
    log.info("Klien CRM ditambahkan: %d", crm.seed_if_empty())
    BUNDLES = model.load_all()
    if len(BUNDLES) < len(crm_data.TARGET_ORDER):
        log.info("Model belum lengkap, menjalankan analysis.run() (sekitar 1-2 menit)...")
        import analysis
        analysis.run()
        BUNDLES = model.load_all()

    app = Application.builder().token(config.BOT_TOKEN).build()
    for name, fn in [("start", start_cmd), ("help", help_cmd), ("klien", klien_cmd), ("prediksi", prediksi_cmd),
                     ("fitur", fitur_cmd), ("riwayat", riwayat_cmd), ("analisis", analisis_cmd), ("stats", stats_cmd)]:
        app.add_handler(CommandHandler(name, fn))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    log.info("Bot berjalan. Tekan Ctrl+C untuk berhenti.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
