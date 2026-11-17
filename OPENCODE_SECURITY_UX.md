# Prompt OpenCode — Peningkatan Keamanan dan UX

Kamu adalah software engineer yang bekerja pada repository `xexoxexo/knn-smartmoney-crm-bot`. Fokus tugas ini hanya pada **keamanan akses, privasi data, validasi input, dan pengalaman pengguna (UX)**. Jangan melakukan perubahan pada model machine learning, aturan bisnis, ambang prediksi, atau evaluasi model kecuali perubahan kecil benar-benar diperlukan untuk mencegah penyajian hasil yang menyesatkan; jika demikian, jelaskan alasannya dan tambahkan tes.

## Konteks aplikasi

Aplikasi ini adalah chatbot Telegram untuk CRM keuangan. Fitur yang ada antara lain pencarian klien, prediksi indikator, input prediksi manual, riwayat, statistik, evaluasi model, dan pertanyaan bebas melalui NLP. Periksa implementasi aktual sebelum membuat perubahan; nama file yang mungkin relevan termasuk `bot.py`, `crm.py`, `crm_data.py`, `config.py`, `model.py`, file NLP, README, dan tes.

Data CRM dapat berisi informasi keuangan sensitif. Data sintetis yang tersedia adalah simulasi dan bukan bukti performa pada data nyata. Jangan mengklaim aplikasi siap untuk peluncuran publik atau memberi saran investasi.

## Cara bekerja

1. Periksa struktur repo, konfigurasi, dependensi, alur handler Telegram, akses database, log, dan tes yang sudah ada.
2. Sampaikan ringkasan temuan dan rencana singkat, lalu lanjutkan implementasi tanpa menunggu konfirmasi.
3. Buat perubahan sekecil mungkin dan ikuti pola proyek.
4. Jangan menebak perilaku yang belum diperiksa. Jangan mencetak atau memasukkan token, secret, data klien, atau informasi pribadi ke output, log, dokumentasi, maupun tes.
5. Jangan mengubah data produksi, melakukan commit/push, atau membuat PR.
6. Jalankan tes dan pemeriksaan yang tersedia. Perbaiki kegagalan yang disebabkan perubahan; laporkan hal yang tidak dapat dijalankan.

## 1. Keamanan akses

- Terapkan prinsip **default deny** untuk akses ke data CRM nyata.
- Tambahkan konfigurasi allowlist Telegram user ID melalui environment/config; jangan hardcode ID pengguna atau token.
- Jika data nyata dapat diakses, tolak semua pengguna yang tidak diizinkan. Jika allowlist belum dikonfigurasi, akses ke data nyata harus tetap tertutup.
- Pastikan pemeriksaan akses berlaku konsisten pada semua jalur: command handler dan pertanyaan bebas/NLP, termasuk fitur pencarian klien, prediksi, riwayat, statistik, dan analisis yang terkait data internal.
- Jangan membocorkan keberadaan klien, contoh ID klien, statistik internal, atau detail lain dalam pesan penolakan.
- Pastikan mode demo hanya menggunakan data sintetis dan tidak dapat beralih diam-diam ke database/data nyata. Jika pemisahan mode belum jelas, tambahkan konfigurasi eksplisit dan aman.
- Tulis tes yang mencakup pengguna diizinkan, tidak diizinkan, allowlist kosong, dan akses melalui pertanyaan bebas.
- Dokumentasikan konfigurasi dengan placeholder aman, tanpa nilai rahasia.

## 2. Privasi dan pengelolaan data

- Telusuri apa yang disimpan: teks percakapan, identitas Telegram, riwayat prediksi, dan data klien.
- Minimalkan data yang disimpan. Jangan menyimpan teks mentah percakapan jika tidak dibutuhkan fitur; jangan menaruh konten pesan atau data finansial dalam log.
- Jika skema database perlu berubah, buat perubahan yang kompatibel dan dokumentasikan migrasi. Jangan menghapus tabel/database secara otomatis.
- Bila dapat diterapkan dengan aman, sediakan cara pengguna menghapus riwayat miliknya sendiri dengan konfirmasi. Jangan sampai menghapus data CRM atau data pengguna lain.
- Dokumentasikan data yang dikumpulkan, tujuan penyimpanan, dan batasan penghapusannya. Jangan membuat klaim kepatuhan hukum atau regulasi tanpa audit.
- Tambahkan tes untuk perilaku penyimpanan/penghapusan yang diubah.

## 3. Validasi input

- Validasi input manual dan sumber CSV sebelum fitur atau model memprosesnya.
- Tangani nilai yang tidak numerik, NaN/infinity, kolom tidak dikenal, kolom wajib yang kosong, format rusak, dan nilai yang tidak masuk akal berdasarkan makna kolom.
- Jangan menciptakan aturan bisnis baru atau mengubah ambang label. Jika rentang validitas tidak didefinisikan, gunakan validasi tipe/keberadaan yang konservatif dan dokumentasikan asumsi.
- Pesan kesalahan harus menyebut cara memperbaiki input dan nama kolom yang relevan, tetapi tidak mengulang data sensitif.
- Pastikan input tidak valid tidak menghasilkan prediksi seolah-olah valid.
- Tambahkan tes untuk kasus valid, tidak lengkap, format salah, dan nilai batas.

## 4. UX berbahasa Indonesia

- Perbaiki `/start`, `/help`, pesan kesalahan, dan respons utama supaya pengguna awam tahu cara mulai dan apa yang bisa dilakukan.
- Gunakan bahasa Indonesia sederhana; jelaskan istilah teknis seperti margin laba, rasio biaya, realisasi anggaran, dan dana darurat dengan keterangan singkat.
- Tampilkan satuan dan periode yang jelas. Jangan mencampur nilai tahunan dan bulanan tanpa penjelasan.
- Jika pengguna harus memasukkan data, beri contoh yang mudah diikuti, daftar kolom wajib, satuan, dan contoh input yang aman. Jangan mengandalkan nama kolom internal sebagai satu-satunya panduan.
- Tanggapi perintah/pertanyaan yang tidak dikenali dengan petunjuk langkah berikutnya, bukan pesan yang membingungkan.
- Gunakan istilah yang tidak memberi kesan kepastian: hasil adalah **estimasi model**, bukan fakta atau jaminan. Jangan menyebut probabilitas sebagai tingkat keyakinan terkalibrasi kecuali implementasi memang mendukung interpretasi tersebut.
- Tandai hasil yang menggunakan data sintetis sebagai **DEMO / SIMULASI** dengan jelas.
- Pertahankan peringatan yang mudah dipahami bahwa keluaran bukan saran keuangan atau investasi.
- Jangan menyebut klien sehat/buruk atau menyarankan investasi berdasarkan prediksi saja.
- Pastikan informasi klien serupa tidak ditampilkan kepada pihak yang tidak berhak.

## 5. Dokumentasi dan mode demo

Perbarui README atau dokumentasi yang sesuai agar menjelaskan:
- Cara menjalankan mode demo menggunakan data sintetis.
- Cara mengaktifkan akses terbatas ke data nyata dan mengatur allowlist.
- Konfigurasi baru dan contoh placeholder yang aman.
- Data apa yang disimpan, bagaimana riwayat dihapus jika fitur tersedia, serta batasannya.
- Makna hasil dan peringatan bahwa hasil simulasi tidak membuktikan performa dunia nyata.
- Checklist keamanan sebelum data nyata digunakan: akses terbatas, pengamanan database dan backup, validasi model pada data representatif, tinjauan ahli/domain, serta prosedur penanganan insiden.

Jangan menyatakan sistem siap digunakan secara publik atau telah lolos audit keamanan.

## Kriteria selesai

- Akses ke data nyata tertutup secara default dan hanya dapat dibuka dengan konfigurasi akses eksplisit.
- Semua jalur command dan NLP menerapkan otorisasi yang sama.
- Mode demo dapat dijalankan dengan data sintetis dan ditandai jelas.
- Data sensitif tidak muncul dalam log atau pesan penolakan.
- Input tidak valid ditolak dengan petunjuk yang membantu.
- Respons bot lebih mudah dipahami pengguna awam dan menjelaskan batas estimasi.
- Tes otomatis mencakup akses, validasi, dan privasi sesuai perubahan.
- Dokumentasi sesuai dengan implementasi.

## Laporan akhir

Setelah implementasi, laporkan secara ringkas:
1. Perubahan keamanan dan UX yang dilakukan.
2. File yang diubah.
3. Variabel konfigurasi baru beserta contoh placeholder aman.
4. Tes/perintah pemeriksaan yang dijalankan dan hasilnya.
5. Risiko atau pekerjaan lanjutan yang belum terselesaikan.
6. Cara menjalankan mode demo.
