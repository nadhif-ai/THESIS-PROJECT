# Hasil uji Playground produksi — 28 Oktober 2026

Investigasi lanjutan dengan detail trace dan rancangan solusi: [retrieval-quality-investigation.md](retrieval-quality-investigation.md). Investigasi itu juga memastikan kegagalan cakupan passage dan classifier yang melewati retrieval pada permintaan gambar.

Pengujian manual di `https://chatbotta-nadhif.vercel.app/admin/playground`, sekitar 16.09–16.15 WIB. Pesan menggunakan bahasa Indonesia dan hanya dikirim ke Playground, bukan pelanggan WhatsApp. Ini sampel uji, bukan evaluasi statistik. Jawaban di bawah ditranskripsikan dari tampilan Playground; pemisahan paragraf disesuaikan untuk keterbacaan. Pengujian dilakukan pada snapshot aktif `kb-c771d8efa03c49c6949561488ce70f67`; perubahan knowledge yang belum disinkronkan tidak digunakan.

## Temuan dan investigasi

1. **Jam buka, alamat, kontak, dan alur pemesanan tidak terjawab lengkap karena sumber SOP tidak ada di snapshot aktif.** Halaman Knowledge menampilkan 5 sumber aktif, 128 passage, sinkronisasi terakhir 27 Oktober 2026 23.29 WIB, dan perubahan yang menunggu sinkronisasi. Pembacaan manifest versi published secara read-only memastikan sumber aktif hanya `02_spesifikasi_bahan_dan_finishing.txt`, `03_panduan_berkas_siap_cetak.txt`, `04_daftar_estimasi_harga.txt`, `05_daftar_pertanyaan_populer.txt`, dan `06_estimasi_pcs_per_lembar_a3.txt`: `01_sop_dan_kebijakan_toko.txt` tidak ada. Source SOP yang disiapkan di halaman Knowledge aktif untuk sync berikutnya, diperbarui 23.37 WIB, dan preview berisi alamat, jam layanan, kontak, dan alur pesanan. Karena file itu tidak diindeks dalam snapshot aktif, reranking tidak bisa menemukannya. Ini menjelaskan kegagalan di uji ini; belum membuktikan apa yang menyebabkan SOP dikeluarkan saat sync sebelumnya.
2. **Jawaban mengarahkan ke admin tanpa memberikan cara menghubunginya.** Pada uji jam buka dan kontak, chatbot menyatakan data tidak ada dan meminta konfirmasi ke admin. Email dari dokumen lain memang dapat ditemukan, tetapi bukan jawaban atas nomor dan alamat. Hasil Inspect memperlihatkan sumber lain, bukan SOP. Data sumber lokal dan preview staged berbeda untuk nomor admin pertama; verifikasi dengan pemilik toko sebelum dianggap benar.
3. **Roll Up Banner dan konteks jumlah bekerja pada sampel ini.** Harga pada passage aktif Rp195.000 per paket untuk Flexi China 280 GSM 60×160, termasuk rangka. Perhitungan 2 = Rp390.000 dan 3 = Rp585.000 benar. Penyelesaian pemesanan tetap terbatas oleh SOP yang tidak aktif.
4. **Pertanyaan lanjutan ikut memuat riwayat ke query retrieval.** Trace jam buka menunjukkan query ditambah pertanyaan sebelumnya; `app/backend/history.py` menambahkan hingga tiga pesan pelanggan untuk pertanyaan pendek dan `app/backend/chain.py` meneruskannya ke pencarian. Ini berpotensi memengaruhi ranking, tetapi bukan penyebab yang perlu diasumsikan untuk kegagalan SOP yang terbukti tidak terindeks. Uji ulang setelah sinkronisasi diperlukan untuk menilai kualitas ranking.

Jangan langsung menyamakan teks staged atau file lokal dengan fakta bisnis yang telah diverifikasi; SOP perlu divalidasi pemilik toko. Sync, pengubahan data, perbaikan kode, dan uji ulang setelah perubahan sengaja tidak dilakukan pada sesi investigasi ini.

## Transkrip uji baru

### 1. Sapaan
**Input:** Halo admin, selamat sore

**Output:** Selamat sore, Kak! 😊 Ada yang bisa saya bantu terkait kebutuhan cetak di Asia Visual?

Inspect: 0 sumber; respons generatif, 5,247 detik.

### 2. Cabang dan layanan
**Input:** Toko ini punya cabang di mana saja? Apa saja layanan cetaknya?

**Output:** Kak, Asia Visual Grafika punya dua cabang, yaitu *Cabang Ciputat* dan *Cabang Pamulang*. Daftar harga yang saya miliki berlaku untuk kedua cabang. Layanan cetak yang tercatat di informasi saya: - *Cetak lembaran A3+ (DocuPrint Laser)* dengan pilihan kertas seperti HVS 100 GSM, Concorde 260 GSM, dan Photopaper 260 GSM. Cocok untuk dokumen, laporan, sertifikat, atau brosur. - *Brosur, flyer, dan pamflet*, dengan perhitungan yang menyesuaikan jumlah dan ukuran. - *Merchandise dan produk kustom*, seperti kartu ID Card PVC, tali lanyard (polos, sablon 1 warna, atau full color), serta pin dan gantungan kunci. Untuk produk di luar itu, seperti jilid khusus, emboss, atau finishing rumit, saya belum punya datanya. Silakan langsung tanyakan ke admin toko. Alamat lengkap dan kontak masing-masing cabang belum ada di informasi saya, jadi akan saya cek ke admin. Kalau Kakak mau, sebutkan dulu area Kakak supaya bisa saya bantu memilih cabang yang sesuai.

Inspect: 5 passage, dari dokumen harga, panduan berkas, dan spesifikasi, tidak ada SOP. Jawaban cabang benar tetapi alamat dan kontak tidak tersedia di konteks.

### 3. Jam operasional
**Input:** Jam operasional toko dari jam berapa sampai jam berapa untuk setiap hari?

**Output:** Maaf, Kak, informasi jam operasional toko belum tersedia di data saya, jadi saya belum bisa memastikan jam bukanya untuk tiap hari. Untuk memastikannya, Kakak bisa tanyakan langsung ke admin toko. Kalau Kakak sudah memilih cabang, saya bisa bantu lanjutkan informasinya setelah itu.

Inspect: 5 passage spesifikasi, panduan berkas, dan harga; tidak ada SOP. [Trace](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/ac00eeb0-7d99-4513-92fe-9e366ae6b9e8/trace/01a181c6-51ce-71b2-ac3a-d521f1b59298/run/01a181c6-51ce-71b2-ac3a-d521f1b59298).

### 4. Nomor admin dan alamat
**Input:** Kalau begitu, berapa nomor WhatsApp admin dan alamat cabang Ciputat?

**Output:** Maaf, Kak, nomor WhatsApp admin dan alamat Cabang Ciputat belum tersedia di data saya, jadi saya belum bisa memastikannya. Silakan konfirmasi ke admin toko untuk kontak dan alamatnya. Sebagai informasi, email Cabang Ciputat adalah asiavisualgrafika@gmail.com. Email ini bisa dipakai untuk mengirim berkas desain. Subjek emailnya sebaiknya: [Nama Pemesan] - [Jenis Pesanan & Ukuran] - [Nomor WhatsApp].

Inspect: 5 passage; hasil pertama panduan pengiriman berkas, tanpa SOP.

### 5. Estimasi Roll Up Banner
**Input:** Saya mau pesan roll up banner ukuran 60 x 160 cm, bahan flexi china 280 gsm sebanyak 2 buah. Berapa totalnya dan sudah termasuk rangka?

**Output:** Baik, Kak. Untuk pesanan Kakak, berikut estimasinya: *Roll Up Banner Flexi China 280 GSM ukuran 60x160 cm* - Harga: Rp 195.000 per paket - Jumlah: 2 buah - Total: 2 × Rp 195.000 = *Rp 390.000* Harga per paket ini sudah termasuk cetak dan rangka/tiang gulung otomatis, jadi tidak perlu ditambah biaya rangka terpisah. Totalnya juga sudah dibulatkan ke kelipatan Rp 500, sehingga tetap Rp 390.000. Harga ini masih estimasi. Untuk kepastian harga dan pengecekan file desain, silakan konfirmasi ke admin toko. Kalau Kakak mau melanjutkan, sebutkan dulu cabang yang paling nyaman, yaitu Cabang Ciputat atau Cabang Pamulang.

Inspect: 5 passage harga; passage pertama mendukung harga dan rangka.

### 6. Perubahan jumlah dan cabang
**Input:** Kalau jumlahnya jadi 3 buah, totalnya berapa? Saya pilih cabang Ciputat, bagaimana langkah pemesanannya?

**Output:** Baik, Kak. Untuk 3 buah Roll Up Banner 60x160 cm dengan bahan Flexi China 280 GSM, perhitungannya: *Roll Up Banner Flexi China 280 GSM ukuran 60x160 cm* - Harga: Rp 195.000 per paket (sudah termasuk cetak dan rangka gulung) - Jumlah: 3 buah - Total: 3 × Rp 195.000 = *Rp 585.000* Total ini sudah kelipatan Rp 500, jadi tidak ada pembulatan tambahan. Untuk pesanan Kakak, Cabang Ciputat sudah dipilih. Alamat dan kontak Cabang Ciputat belum tersedia di data saya, jadi silakan konfirmasi ke admin toko untuk lokasi dan nomor yang bisa dihubungi. Langkah selanjutnya: 1. Siapkan file desain sesuai ukuran 60x160 cm. 2. Bawa atau kirim file tersebut ke Cabang Ciputat, lalu minta admin memeriksa file, harga, dan jadwal pengerjaan. Ringkasan kebutuhan Kakak: - Produk: Roll Up Banner 60x160 cm - Bahan: Flexi China 280 GSM - Jumlah: 3 buah - Cabang: Ciputat - Estimasi: Rp 585.000 (harga perlu dikonfirmasi admin) Ini baru ringkasan kebutuhan, belum berarti pesanan sudah masuk antrean cetak. Admin toko yang akan mengonfirmasi kelanjutannya.

Inspect: 5 passage harga. Perhitungan dan ingatan spesifikasi benar; lokasi dan kontak tidak dapat disampaikan.

### 7. Gambar Roll Up
**Input:** Boleh kirim gambar roll up banner yang tadi?

**Output:** Ini ilustrasi roll up banner, Kak. Ukuran dan spesifikasi mengikuti pesanan. Harga dan spesifikasi yang belum terkonfirmasi dapat ditanyakan ke admin.

**Media:** Playground menampilkan gambar berlabel “Roll Up Banner 60 × 160 cm dengan kaset gulung aluminium dan tiang penyangga.” dengan keterangan “Ilustrasi produk; model dan finishing dikonfirmasi admin. · Preview only”. Inspect menunjukkan 0 passage. Pengiriman WhatsApp aktual tidak diuji.

### 8. Gambar perbandingan tujuh kertas
**Input:** Sekarang saya mau lihat gambar perbandingan tujuh pilihan bahan kertas untuk cetak digital A3+. Bisa kirim?

**Output:** Ini ilustrasi digital print, Kak. Ukuran dan spesifikasi mengikuti pesanan. Harga dan spesifikasi yang belum terkonfirmasi dapat ditanyakan ke admin.

**Media:** Playground menampilkan gambar “Perbandingan bentuk tujuh pilihan bahan kertas yang tersedia pada ukuran panel yang sama.” dengan keterangan “Contoh Bahan Kertas Digital Printing A3+ · Preview only”. Katalog menandai gambar aktif dan sebagai ilustrasi AI. Inspect menunjukkan 0 passage dan teks “Greetings and menu replies do not require knowledge search”, meskipun ini permintaan gambar, sehingga penjelasan panel evidence menyesatkan. Pengiriman WhatsApp aktual tidak diuji.

### 9. Perbandingan bahan dan estimasi sertifikat
**Input:** Apa bedanya ketujuh kertas itu? Saya ingin cetak 20 lembar sertifikat, bahan mana yang cocok dan berapa perkiraan harganya?

**Output:** Kak, dari data yang saya miliki, tidak semua dari tujuh pilihan bahan itu bisa saya jelaskan lengkap. Berikut yang tersedia: - *Linen 230 GSM*: permukaannya bergaris halus bersilang seperti kain tenun, sehingga kesannya eksklusif dan premium. Ketebalannya sama dengan BW 230 GSM. Cocok untuk sertifikat kelulusan formal dan piagam

Jawaban berhenti pada kata “piagam” tanpa menyelesaikan perbandingan atau estimasi. Inspect: 5 passage dari spesifikasi dan harga. [Trace](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/ac00eeb0-7d99-4513-92fe-9e366ae6b9e8/trace/01a181c8-d63d-7352-97b4-5c66f200f589/run/01a181c8-d63d-7352-97b4-5c66f200f589) menunjukkan `finish_reason=length`, `max_completion_tokens=2048`, total 2048 output token, termasuk 1886 reasoning token. Ini batas output yang habis, bukan bukti bahwa hanya satu bahan tersedia. Di source saat ini `app/backend/models.py:145` menetapkan batas 2048 untuk model jawaban; `app/backend/chain.py:695` mendeteksi truncation tetapi fallback diterapkan hanya dalam cabang `media_response`, sehingga jawaban teks terpotong diteruskan. Trace mencatat commit produksi `edaa20652fb37d4f303e2dd236c191faea685f8c`. Satu contoh belum menunjukkan frekuensi kegagalan.

## Temuan tambahan untuk sesi perbaikan

- **Prioritas tinggi:** jawaban teks terpotong disajikan sebagai jawaban selesai saat model mencapai batas output. Kasus 9 membuktikan penyebab langsung dan jalur tanpa fallback di kode; perlu uji regresi pada jawaban panjang dan model dengan reasoning sebelum menentukan perubahan.
- **Prioritas rendah:** panel Inspect menampilkan penjelasan sapaan/menu untuk semua hasil dengan nol passage (`frontend/src/App.tsx:948`), termasuk dua permintaan gambar. Hasil visual berfungsi tetapi penjelasan evidence tidak sesuai kasus.
- **Prioritas investigasi:** setelah SOP yang benar dipastikan dan disinkronkan pada sesi berikutnya, ulangi pertanyaan jam buka, nomor, alamat, dan pesanan dengan maupun tanpa riwayat; periksa manifest, passage, trace, dan jawaban. Jangan menyimpulkan sinkronisasi sendirian menyelesaikan semua masalah ranking sebelum uji ulang.

## Uji mandiri tanpa riwayat

### 10. Jam operasional
**Input:** Jam operasional toko hari Senin sampai Minggu berapa?

**Output:** Maaf, Kak, informasi jam operasional toko untuk hari Senin sampai Minggu belum tersedia di data saya, jadi saya belum bisa memastikannya. Untuk memastikan jam buka, Kakak bisa menanyakan langsung ke admin toko. Kalau Kakak sudah memilih cabang, saya juga bisa bantu menyiapkan informasi cabangnya.

Inspect: lima passage dari spesifikasi, panduan berkas, dan harga; tidak ada SOP. Kegagalan juga terjadi tanpa riwayat. [Trace](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/ac00eeb0-7d99-4513-92fe-9e366ae6b9e8/trace/01a181c9-9971-74f0-9cff-31110bf29ff4/run/01a181c9-9971-74f0-9cff-31110bf29ff4).

## Konteks dari percakapan yang sudah terbuka

Sebelum uji baru, Playground sudah menampilkan percakapan milik pengguna: `Hi admin` menghasilkan sapaan/menu otomatis; pertanyaan jumlah cabang dijawab dua cabang; `Jam bukanya tuh kapan detailnya` dijawab bahwa jam buka tidak tersedia, disertai email dua cabang. Inspect menampilkan lima passage tanpa SOP. Trace mengonfirmasi query jam buka menyertakan dua pesan pelanggan sebelumnya. Screenshot WhatsApp yang diberikan pengguna adalah laporan gejala terpisah, bukan pengujian WhatsApp baru dalam sesi ini.

## Verifikasi setelah pemulihan SOP — 28 Oktober 2026

Snapshot baru `kb-0f089af2f6ca4d1391185ae8d91dc790` aktif pada 16.38.57 WIB dengan enam sumber dan 142 passage. Pengujian berikut masih menggunakan runtime produksi lama setelah sync data; perbaikan kode baru tersedia lokal.

### 11. Jam operasional setelah sync
**Input:** Jam operasional toko hari Senin sampai Minggu berapa?

**Output:** Berikut jam layanan toko, Kak (WIB): - *Senin–Sabtu:* 08.30–02.30 dini hari. Pesanan baru ditutup pukul 01.30. Setelah itu hanya penyelesaian cetak dan pengambilan sampai 02.30. - *Minggu:* 09.00–21.00. Close order pukul 20.30. Untuk hari libur nasional, jamnya berbeda: 12.00–21.00 pada umumnya, dan khusus hari Jumat mulai 13.00 (setelah shalat Jumat) sampai 21.00.

Inspect: lima passage SOP; passage pertama mencakup jadwal dan close order. [Trace](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/ac00eeb0-7d99-4513-92fe-9e366ae6b9e8/trace/01a181e1-f83d-7bc3-89f5-6ee44a89655a/run/01a181e1-f83d-7bc3-89f5-6ee44a89655a?start_time=2026-10-28T09%3A40%3A32.445362%2B00%3A00).

### 12. Kontak dan alamat setelah sync
**Input:** Berapa nomor WhatsApp admin dan alamat cabang Ciputat?

**Output:** Berikut kontak admin dan alamat cabang Ciputat, Kak: *Nomor WhatsApp Admin:* - Admin 1: 0896-9241-1115 - Admin 2: 0897-3232-322 *Alamat Cabang Ciputat Timur (cabang utama):* Jl. Ir. H. Juanda No. 17, Cempaka Putih, Kec. Ciputat Timur, Kota Tangerang Selatan, Banten 15419. Patokan: tepat di seberang SPBU (Pom Bensin) Ciputat. Peta: https://maps.app.goo.gl/Z4MSgYVkeJ7MTHKdA Kalau mau sekalian kirim berkas desain untuk cabang Ciputat, bisa lewat email ke asiavisualgrafika@gmail.com dengan subjek [Nama Pemesan] - [Jenis Pesanan & Ukuran] - [Nomor WhatsApp].

Inspect: lima passage; SOP dan panduan berkas. Nomor mengikuti source admin yang aktif, bukan file lokal. [Trace](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/ac00eeb0-7d99-4513-92fe-9e366ae6b9e8/trace/01a181e3-26dd-7f30-b95a-0ff46373b29a/run/01a181e3-26dd-7f30-b95a-0ff46373b29a?start_time=2026-10-28T09%3A41%3A49.917426%2B00%3A00).

Pengujian generasi lokal berikutnya dicatat terpisah di [retrieval-generation-smoke.json](retrieval-generation-smoke.json), lengkap dengan enam input/output dan trace. Itu bukan pengujian UI produksi terhadap kode yang belum dideploy.
