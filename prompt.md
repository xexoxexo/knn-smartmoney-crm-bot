Kamu adalah software engineer yang bertugas meningkatkan kesiapan penggunaan aplikasi ini oleh pengguna umum.

REPOSITORY
https://github.com/xexoxexo/knn-smartmoney-crm-bot

KONTEKS
Aplikasi ini adalah chatbot Telegram untuk CRM keuangan. Fitur yang terlihat mencakup pencarian klien, prediksi indikator keuangan dengan KNN, prediksi dari input manual, riwayat, statistik, evaluasi model, dan pemahaman pertanyaan sederhana dengan NLP.

Beberapa bagian yang sudah diketahui:
- bot.py menangani perintah Telegram seperti /klien, /prediksi, /fitur, /riwayat, /analisis, dan /stats.
- crm.py menyimpan data klien, pengguna bot, interaksi, dan prediksi.
- crm_data.py mendefinisikan skema data, fitur turunan, ambang aturan bisnis, dan data simulasi.
- README menyebut data sintetis sebagai simulasi, bukan temuan empiris.
- Aplikasi menggunakan data keuangan, sehingga keamanan dan privasi harus menjadi prioritas.

TUJUAN
Tingkatkan aplikasi agar lebih aman dan mudah dipahami untuk uji coba dengan pengguna umum. Jangan mengklaim bahwa aplikasi sudah aman untuk peluncuran publik atau layak memberi saran investasi. Jika arsitektur saat ini belum mendukung penggunaan publik yang aman, pertahankan akses tertutup secara default dan jelaskan batasannya.

ALUR KERJA WAJIB
1. Periksa struktur repo, README, konfigurasi, dependensi, seluruh alur bot/CRM/model, serta tes yang sudah ada sebelum mengubah kode.
2. Ringkas temuan awal dan rencana singkat, lalu lanjutkan implementasi tanpa menunggu persetujuan.
3. Ikuti gaya dan pola yang sudah digunakan repo. Hindari perubahan besar yang tidak diperlukan.
4. Jangan menebak konfigurasi atau perilaku model. Baca implementasi terkait sebelum memutuskan.
5. Jangan mengubah ambang bisnis, definisi “smart money”, label, atau algoritma model tanpa alasan kuat dan dokumentasi.
6. Jangan menambahkan layanan berbayar atau dependensi besar kecuali benar-benar diperlukan.
7. Jangan menampilkan, menulis, atau mengirim secret/token. Jangan menyalin data sensitif ke log, tes, atau dokumentasi.
8. Jangan commit, push, membuat PR, atau mengubah pengaturan Git kecuali diminta secara eksplisit.
9. Setelah perubahan, jalankan tes dan pemeriksaan yang tersedia. Jika ada yang gagal, perbaiki bila terkait perubahan; jika tidak bisa dijalankan, jelaskan penyebabnya.

PRIORITAS IMPLEMENTASI

A. AKSES AMAN — DEFAULT DENY
- Periksa konfigurasi dan alur akses Telegram yang ada.
- Tambahkan mekanisme allowlist Telegram user ID yang mudah dikonfigurasi melalui environment/config, tanpa menyimpan daftar rahasia di source code.
- Dalam mode yang memakai data CRM nyata, tolak akses jika allowlist belum dikonfigurasi atau pengguna tidak terdaftar.
- Lindungi semua perintah yang dapat membuka data atau statistik, termasuk /klien, /prediksi bila relevan, /riwayat, /analisis, /stats, serta pertanyaan bebas yang memicu fitur tersebut.
- Pesan penolakan harus ramah dan tidak membocorkan apakah klien tertentu ada.
- Jangan tampilkan contoh ID klien nyata kepada pengguna yang tidak berwenang.
- Pastikan mode demo dengan data sintetis tetap bisa dijalankan tanpa membuka akses ke data CRM nyata. Jika struktur konfigurasi saat ini tidak cukup untuk membedakan mode demo dan data nyata, tambahkan konfigurasi yang eksplisit dan aman.
- Dokumentasikan cara mengatur mode demo dan allowlist. Jangan menaruh token bot atau ID pengguna nyata dalam contoh.

B. PRIVASI DAN MINIMISASI DATA
- Tinjau penyimpanan teks interaksi mentah di CRM. Minimalkan atau hentikan penyimpanan isi pesan bila tidak diperlukan untuk fungsi aplikasi.
- Jangan mencatat isi pesan pengguna, data finansial, token, atau informasi pribadi ke log aplikasi.
- Pertahankan fungsi fitur yang ada sebisa mungkin. Jika perubahan skema database diperlukan, buat migrasi atau prosedur peningkatan yang aman dan terdokumentasi; jangan menghapus database pengguna secara otomatis.
- Sediakan penjelasan privasi yang jelas dalam bahasa Indonesia: data apa yang disimpan, untuk apa, dan batasan penghapusannya.
- Jika memungkinkan dengan desain yang ada, sediakan cara pengguna menghapus riwayat/interaksi miliknya sendiri dengan konfirmasi yang jelas. Penghapusan data seorang pengguna tidak boleh menghapus data klien milik CRM atau data pengguna lain.
- Jangan menyatakan bahwa aplikasi memenuhi hukum/regulasi privasi tertentu tanpa audit yang memadai.

C. VALIDASI INPUT DAN KEANDALAN
- Periksa input /prediksi dan data CSV sebelum diproses.
- Tolak nilai non-numerik, NaN, tak hingga, nilai negatif yang tidak masuk akal untuk kolom terkait, kolom tidak dikenal, dan input yang tidak lengkap.
- Berikan pesan kesalahan yang menyebut kolom/format yang perlu diperbaiki, tanpa membocorkan data sensitif.
- Pastikan model tidak menghasilkan prediksi dari data yang tidak cukup atau tidak valid.
- Periksa penanganan data kosong atau rasio yang tidak terdefinisi di pipeline fitur.
- Tambahkan tes untuk validasi input dan kasus batas.
- Jangan mengubah aturan domain secara diam-diam. Jika batas validitas belum jelas, gunakan pemeriksaan konservatif dan dokumentasikan asumsi.

D. PENJELASAN HASIL YANG JUJUR DAN MUDAH DIPAHAMI
- Ganti atau lengkapi istilah teknis pada jawaban bot dengan bahasa Indonesia sederhana.
- Jelaskan arti indikator seperti margin laba, dana darurat, realisasi anggaran, dan rasio biaya.
- Tampilkan satuan dan periode dengan jelas; bedakan juta Rupiah per tahun dengan nilai bulanan.
- Jelaskan bahwa hasil adalah estimasi model, bukan fakta atau jaminan.
- Jangan menyebut nilai probabilitas sebagai “tingkat keyakinan” kecuali implementasi model benar-benar mendukung interpretasi tersebut. Periksa model.py dan jelaskan makna angka yang benar; jika tidak terkalibrasi, gunakan label yang lebih tepat atau hilangkan angka tersebut.
- Tandai dengan jelas hasil dari data sintetis sebagai DEMO/SIMULASI.
- Pertahankan peringatan bahwa hasil bukan saran keuangan/investasi, dan buat lebih mudah dipahami.
- Jangan menyimpulkan bahwa suatu klien “sehat”, “buruk”, atau “harus berinvestasi” hanya dari prediksi model.
- Jangan menampilkan daftar klien serupa jika itu dapat mengungkap data klien lain kepada pengguna yang tidak berhak.

E. PENGGUNAAN YANG LEBIH MUDAH
- Perbaiki /start dan /help agar pengguna awam tahu langkah pertama.
- Berikan contoh pertanyaan/perintah yang aman, daftar fitur dengan istilah awam, serta petunjuk format data.
- Pertahankan perintah teknis untuk operator bila perlu, tetapi jangan jadikan nama kolom internal seperti total_revenue sebagai satu-satunya cara pengguna umum memasukkan data.
- Jika menambahkan alur input bertahap atau menu, buat perubahan sederhana dan konsisten dengan library Telegram yang sudah dipakai.
- Pastikan respons untuk perintah tidak dikenal dan input salah membantu pengguna memperbaiki kesalahan.

F. DOKUMENTASI
Perbarui README dalam bahasa Indonesia dengan:
- Siapa pengguna yang dituju dan batas penggunaan aplikasi.
- Cara menjalankan mode demo.
- Cara mengaktifkan akses terbatas untuk data nyata.
- Variabel konfigurasi baru dan contoh aman tanpa secret.
- Arti hasil prediksi dan metrik yang ditampilkan.
- Data apa yang disimpan dan panduan privasi/penghapusan.
- Pernyataan bahwa data sintetis hanya untuk demonstrasi dan tidak membuktikan performa di dunia nyata.
- Checklist sebelum memakai data finansial nyata: validasi model pada data representatif, tinjauan ahli/domain, kontrol akses, keamanan database, backup, dan prosedur insiden.
Jangan menulis klaim bahwa sistem siap dipakai publik secara luas atau telah lolos audit keamanan.

KRITERIA SELESAI
- Mode demo dapat dijalankan tanpa akses ke data CRM nyata dan diberi label simulasi dengan jelas.
- Data CRM nyata tidak dapat diakses melalui bot tanpa konfigurasi akses yang eksplisit dan valid.
- Perintah serta pertanyaan bebas tunduk pada pemeriksaan akses yang sama.
- Kesalahan input ditangani dengan pesan yang mudah dipahami dan tidak menyebabkan prediksi menyesatkan.
- Informasi sensitif tidak muncul di log baru.
- Jawaban bot menjelaskan batas prediksi dengan bahasa awam.
- Tes otomatis mencakup akses ditolak/diizinkan, validasi input, dan perubahan privasi yang dibuat.
- README menjelaskan setup dan batasan terbaru.
- Tes dan pemeriksaan yang tersedia berhasil, atau hasil dan hambatannya dilaporkan dengan jelas.

BATASAN PENTING
- Jangan membuat bot terbuka untuk siapa saja apabila data CRM nyata dapat diakses.
- Jangan menghapus atau mengubah data produksi secara otomatis.
- Jangan mengarang hasil evaluasi model atau membuat klaim akurasi.
- Jangan menganggap data sintetis sebagai bukti performa nyata.
- Jangan mengubah skema input, ambang, atau definisi bisnis tanpa dokumentasi dan tes.
- Jika satu fitur tidak aman untuk dibuat publik dengan arsitektur saat ini, pertahankan pembatasan akses dan jelaskan alasan serta langkah lanjutan yang diperlukan.

OUTPUT AKHIR
Setelah implementasi, laporkan:
1. Ringkasan perubahan.
2. File yang diubah dan tujuan tiap perubahan.
3. Konfigurasi environment baru beserta contoh placeholder yang aman.
4. Tes/perintah pemeriksaan yang dijalankan dan hasilnya.
5. Fitur atau risiko yang masih belum terselesaikan.
6. Langkah menjalankan demo secara lokal.

Mulai dengan memeriksa repo, lalu implementasikan perubahan yang paling aman dan bernilai tanpa menunggu konfirmasi.
