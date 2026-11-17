# Analisis KNN dalam Memprediksi Pola Smart Money pada Chatbot CRM

Implementasi sistem yang diusulkan pada naskah SLR: **KNN** memprediksi kondisi keuangan klien
(termasuk label **smart money**) dari data **CRM**, dan hasilnya disajikan lewat **ChatBot Telegram**.
Pesan pengguna dipahami dengan NLP (TF-IDF + KNN).

## Kesesuaian dengan naskah

| Bagian naskah | Di project ini |
|---|---|
| **RQ1** varian & parameter KNN | `analysis.py`: grid search K (1–31), metrik jarak (Euclidean/Manhattan/Chebyshev), pembobotan (uniform/distance) |
| **RQ2** fitur data CRM | `crm_data.py`: 17 kolom mentah → 15 fitur (rasio margin, pertumbuhan, volatilitas, dst. sesuai **Tabel 5**) |
| **RQ3** metrik & pembanding | Akurasi, presisi, recall, F1, AUC-ROC; pembanding **Naive Bayes** dan **Random Forest** |
| **RQ4** integrasi ChatBot + CRM | `bot.py` + `crm.py`: bot membaca data klien dari basis data CRM, memprediksi, mencatat interaksi & prediksi |
| **RQ5** definisi smart money | Target `smart_money` = pengelolaan dana cerdas: ≥ 6 dari 7 indikator sehat (lihat di bawah) |
| Rekomendasi evaluasi | k-fold CV (`CV_FOLDS`=5/10), normalisasi (MinMax/Standard), **SMOTE** (hanya pada data latih tiap fold), grid search k |
| Arsitektur (Gambar 2) | Database CRM → fitur → KNN → Telegram Bot API. DB lewat SQLAlchemy: SQLite default, PostgreSQL/MySQL cukup ganti `DATABASE_URL` |

**Smart money (operasional):** klien dihitung sehat pada 7 indikator — laba tinggi, dana darurat memadai,
sesuai anggaran, peluang investasi tinggi, kontrol biaya terjaga (rasio biaya < 75%), risiko anggaran rendah,
beban gaji wajar. Smart money = minimal 6 indikator terpenuhi. Ambang ada di `crm_data.TH`.

**Tabel 5:** 9 target dari tabel (laba, peluang investasi, risiko anggaran, komoditas, dana darurat, anggaran,
pengeluaran bulanan, kontrol biaya, gaji) + target `smart_money`. Satu model KNN dilatih per target.
Catatan: pada Tabel 5 naskah, baris "Risiko Anggaran" dan "Investasi Emas/Bitcoin/BBCA" sama-sama bertarget
`prefers_commodity_investment`; di sini baris Risiko Anggaran dibuat menjadi `high_budget_risk`.
Kolom pendukung ditambahkan agar transformasi Tabel 5 dapat dihitung: `total_revenue`, `profit_prev_year`,
`invest_proposals_value`, `annual_budget_prev`, `monthly_expenses_std`.

## Menjalankan

```bash
pip install -r requirements.txt
cp .env.example .env        # isi TELEGRAM_BOT_TOKEN dari @BotFather
python analysis.py          # grid search + evaluasi + simpan 10 model + laporan (±1–2 menit)
python bot.py               # klien CRM diisi otomatis saat pertama kali jalan
```

Perintah bot: `/klien izaki`, `/prediksi total_revenue=5000 total_profit=1400 ...`, `/fitur`, `/riwayat`,
`/analisis`, `/stats`, atau teks bebas seperti *"apakah klien 12 smart money?"*, *"klien 8 punya dana darurat?"*.

## Memakai data sendiri

Set `DATA_SOURCE=csv` dan `CSV_PATH`. CSV wajib berisi `client_id` + 17 kolom mentah (`crm_data.RAW_COLS`,
juta Rp/tahun). Kolom target (`smart_money`, dst.) opsional; jika tidak ada, label dihitung dari aturan
bisnis `crm_data.TH`. Dataset publik naskah (Telco Churn, Bank Marketing) perlu dipetakan dulu ke kolom ini
atau skema fiturnya disesuaikan.

## Keluaran `analysis.py` (folder `reports/`)

`metrics.json`, `grid_results.csv`, `tabel_perbandingan_model.csv`, `all_targets.csv`, `k_vs_f1.png`
(pengaruh K, metrik, dan SMOTE), `roc_curve.png`, `confusion_matrix.png`. Model tersimpan di `models/`.

## Keterbatasan

- Mode `synthetic` adalah **data simulasi** untuk menguji pipeline; angkanya bukan temuan empiris.
  Label simulasi diturunkan dari aturan dan diberi derau (`LABEL_NOISE`). Untuk laporan, gunakan data perusahaan
  atau dataset publik yang dipetakan.
- Label smart money adalah definisi operasional, bukan label dari pakar. Idealnya divalidasi analis keuangan.
- Hasil pembandingan bisa menunjukkan KNN tidak selalu terbaik; laporkan apa adanya.
- Akurasi intent NLP (leave-one-out) bergantung pada korpus `data/intents.json`; tambah pola untuk menaikkannya.
- Keluaran adalah pendukung keputusan, bukan saran investasi. Pertimbangkan autentikasi pengguna bot dan
  enkripsi data bila dipakai pada data keuangan nyata.
