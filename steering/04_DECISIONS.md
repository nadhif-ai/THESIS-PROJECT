# 04_DECISIONS.md — Log Keputusan Arsitektur & Scope Terkunci

> 📌 **ACUAN TERAKHIR ARCHITECTURE & METRIK (SUPERSEDED BY DEC-016 & PEMAHAMAN_SISTEM.MD):**
> Seluruh keputusan arsitektur sistem dan metrik telah **DIKUNCI MATI (DEC-016)** sebagai berikut:
> 1. Platform: **WhatsApp Webhook API** (Telegram dibuang/superceded).
> 2. Knowledge Base: **6 Dokumen Teks (`01_` s.d. `06_`)**.
> 3. Perhitungan Harga: Langsung diproses oleh **LLM Gemini 2.5 Flash** (Kalkulator web dibuang/superceded).
> 4. Evaluasi Bab V (4 Metrik): Black Box (10 Skenario), Hit Rate@3=100.0% & Precision@3=56.67% (10 Pertanyaan Acuan), SUS (20 Responden), Human Evaluation.

> 📌 **UNTUK APA FILE INI:** Rekaman keputusan teknis, arsitektur RAG, metrik pengujian, dan batasan scope yang sudah disegel.


## DEC-001 — Research Direction
Status: ACTIVE

Keputusan:
Melanjutkan penelitian RAG yang sudah ada.

Alasan:
- sudah sampai tahap Semhas;
- PA menyarankan melanjutkan;
- mengulang penelitian akan menambah konsekuensi akademik.

Catatan:
Perubahan total penelitian tidak dilakukan tanpa konsultasi akademik.

---

## DEC-002 — RAG Complexity
Status: ACTIVE

Keputusan:
Gunakan Naive RAG terlebih dahulu.

Tidak menggunakan:
- reranker;
- arsitektur agent kompleks;
- multi-agent;
- teknologi tambahan yang tidak diperlukan.

---

## DEC-003 — Price Calculation
Status: ACTIVE

Keputusan:
Jika chatbot membutuhkan perhitungan harga, gunakan Tool Use/function deterministik.

Alur:

User
↓
LLM memahami permintaan
↓
LLM menentukan tool
↓
LLM mengisi parameter
↓
Function menghitung harga
↓
Hasil dikembalikan
↓
LLM menyusun jawaban

Catatan:
LLM tidak menjadi kalkulator utama.

---

## DEC-004 — Dataset
Status: SUPERSEDED by DEC-007

Keputusan Awal:
Gunakan dataset yang sudah tersedia terlebih dahulu.

---

## DEC-005 — Locked Thesis Title
Status: LOCKED 🔒

Keputusan:
Judul resmi skripsi dikunci:
"Implementasi Chatbot Informasi Usaha Percetakan Menggunakan Retrieval-Augmented Generation (Studi Kasus: CV. Asia Visual Grafika)"

Alasan:
- Kata "Layanan" resmi dihilangkan agar penguji tidak menuntut fungsionalitas kasir, pembayaran, atau transaksi e-commerce.
- "RAG" diekstensikan menjadi "Retrieval-Augmented Generation" untuk kepatuhan bobot akademik formal.

---

## DEC-006 — Pemisahan Peran Chatbot RAG dan Telegram Mini App
Status: LOCKED 🔒

Keputusan:
- Chatbot RAG: Murni hanya melayani FAQ, konsultasi spesifikasi bahan cetak, panduan berkas siap cetak (prepress), dan SOP toko menggunakan percakapan bahasa alami.
- Telegram Mini App (price_calculator.html): Disediakan khusus untuk perhitungan dan simulasi tarif/harga cetak secara interaktif.

Alasan Akademik & Teknis:
- Murni demi User Experience (UX) dan kenyamanan pengguna.
- Perhitungan harga cetak membutuhkan parameter terstruktur (panjang, lebar, jenis bahan, jumlah, dan pilihan finishing). Antarmuka formulir visual interaktif jauh lebih praktis, intuitif, dan nyaman bagi pengguna daripada harus mengetik rincian parameter panjang via teks.

---

## DEC-007 — Standardisasi Basis Pengetahuan (Knowledge Base) ke Dokumen Teks Modular
Status: LOCKED 🔒

Keputusan:
Mengganti basis data FAQ format CSV yang terfragmentasi menjadi 4 file dokumen teks (.txt) terstruktur dan modular di dalam folder `dataset/knowledge_base/`:
1. `01_sop_dan_kebijakan_toko.txt`: Profil mitra, jam operasional, alur pemesanan, dan kebijakan komplain.
2. `02_spesifikasi_bahan_dan_finishing.txt`: Katalog bahan outdoor, indoor, digital A3+, stiker, dan opsi finishing (laminasi, mata ayam, selongsong, cutting).
3. `03_panduan_berkas_siap_cetak.txt`: Standar resolusi minimal DPI, format warna CMYK, margin/bleed, dan format berkas (PDF, TIFF, dsb).
4. `04_daftar_estimasi_harga.txt`: Rangkuman tarif dasar resmi produk cetak untuk merespons pertanyaan kisaran harga umum di ruang chat teks.

Alasan:
- Sesuai dengan prinsip dasar RAG (Lewis et al., 2020) yang dirancang untuk dokumen naratif tidak terstruktur (unstructured text), bukan tabel Q&A relasional.
- Memudahkan proses pemotongan teks (chunking) menggunakan RecursiveCharacterTextSplitter.
- Mempermudah pengukuran metrik retrieval (Hit Rate & Precision) di Bab 4 karena metadata file terpisah secara jelas.
- Dokumen harga (pricing_table.csv, calculation_rules.csv, product_master.csv) tetap dipertahankan untuk melayani backend kalkulator Telegram Mini App.

---

## DEC-008 — Integrasi Multi-Channel WhatsApp (Fonnte) & Aturan Routing Kalkulator Harga Web
Status: SUPERSEDED by DEC-009

---

## DEC-009 — Penetapan WhatsApp (Fonnte) & Web Portal Kalkulator Sebagai Antarmuka Utama Skripsi
Status: LOCKED 🔒

Keputusan:
1. **Antarmuka Utama Percakapan:** Seluruh pembahasan naskah skripsi (Bab 1 s.d. Bab 5), dokumentasi antarmuka, dan pengujian secara resmi **100% memfokuskan pada WhatsApp Messenger** menggunakan Fonnte Gateway.
2. **Kalkulator Harga Cetak:** Kalkulasi harga interaktif disajikan sebagai **Web Portal Kalkulator Harga Cetak** yang diakses pelanggan via tautan pendek resmi: `https://bit.ly/harga-asia-visual`.
3. **Penyederhanaan Naskah:** Telegram Mini App tidak lagi disebutkan di dalam naskah utama untuk menjaga fokus dan konsistensi naskah skripsi.

---

## DEC-010 — Penghentian Pengembangan Fitur Kode (Code Freeze) & Deadline Mutlak Naskah 10 Oktober 2026
Status: LOCKED 🔒 (MUTLAK & PERMANEN)

Keputusan:
1. **DEADLINE MUTLAK NASKAH UTH:** **10 OKTOBER 2026**. Naskah utuh Bab 1 s.d. Bab 5 wajib selesai 100% sebelum 10 Oktober 2026 agar memiliki waktu yang cukup untuk proses approval/acc 4 tim dosen (Pembimbing 1, Pembimbing 2, Penguji 1, Penguji 2) sebelum batas akhir pendaftaran sidang 11 November 2026.
2. **PENGHENTIAN KODE / FITUR BARU (CODE FREEZE):** Dilarang keras menambah, membahas, atau mengusulkan fitur kodingan baru. Seluruh sistem teknis (FastAPI, ChromaDB Naive RAG, Fonnte WhatsApp, Web Portal Kalkulator) dinyatakan SELESAI & FINAL.
3. **FOKUS TUNGGAL AGENT:** Agent berfokus 100% pada:
   - Penulisan Naskah Utuh Bab 1 s.d. Bab 5 (Target 80+ Halaman SK Rektor No. 69 Tahun 2024).
   - Pembahasan Metode Penelitian & Pipeline Naive RAG.
   - Penulisan Hasil & Analisis Pengujian Empiris.

---

## DEC-011 — Penguncian Metode Pengembangan Sistem (Prototyping Method)
Status: LOCKED 🔒 (PERMANEN)

Keputusan:
Metode Pengembangan Sistem (*Software Development Life Cycle / SDLC*) yang digunakan dalam penelitian skripsi ini secara resmi dikunci menggunakan **Metode Prototyping (*Prototyping Method*)**.

DILARANG KERAS mengubah atau mengganti metode pengembangan sistem (seperti ke Waterfall, Agile/Scrum, atau Extreme Programming).

Alasan Akademik:
1. Tahapan *Prototyping* (Pengumpulan Kebutuhan $\rightarrow$ Perancangan Cepat $\rightarrow$ Konstruksi Prototype $\rightarrow$ Evaluasi Pengguna $\rightarrow$ Perbaikan Prototype) sangat sesuai dengan alur pengembangan Chatbot RAG dan Web Portal Kalkulator.
2. Seluruh artefak perancangan di Bab III dan dokumentasi implementasi di Bab IV & Bab V sudah disusun selaras dengan tahapan *Prototyping Method*.
3. Mengubah metode SDLC pada tahap ini tidak memiliki nilai tambah akademik dan hanya akan merusak konsistensi naskah Bab III & Bab IV.

---

## DEC-012 — Kesepakatan Rencana Aksi 13 Hari Penulisan Naskah Utuh Skripsi (Deadline 10 Oktober 2026)
Status: LOCKED 🔒 (KESEPAKATAN MUTLAK)

Keputusan:
Mahasiswa (Mas Nadif) dan Dosen Pembimbing secara resmi MENYEPAKATI Rencana Aksi 13 Hari Penulisan Naskah Utuh Skripsi (Bab I s.d. Bab VI) menuju batas akhir 10 Oktober 2026.

Lini Masa Eksekusi Harian:
1. **Hari 1–3 (27–29 September 2026):** Penyusunan **BAB IV** (Perancangan & Implementasi) & **BAB V** (Hasil & Pembahasan).
2. **Hari 4–6 (30 September–02 Oktober 2026):** Penyusunan **BAB I** (Pendahuluan).
3. **Hari 7–8 (03–04 Oktober 2026):** Penyusunan **BAB III** (Metode Penelitian).
4. **Hari 9–11 (05–07 Oktober 2026):** Penyusunan **BAB II** (Tinjauan Pustaka & 10 Jurnal Sejenis).
5. **Hari 12–13 (08–09 Oktober 2026):** Penyusunan **BAB VI** (Kesimpulan & Saran) + Merapikan Format Naskah Utuh Minimal 80 Halaman (SK Rektor No. 69 Tahun 2024).
6. **10 OKTOBER 2026:** NASKAH UTUH BAB I - VI SELESAI 100% & SIAP PENUH UNTUK PROSES APPROVAL/ACC 4 DOSEN.

---

## DEC-013 — Spesifikasi Custom Prototyping Method (Tanpa Deployment Cloud Produksi & Tanpa Iterasi Feedback Loop)
Status: LOCKED 🔒 (PERMANEN)

Keputusan:
Metode *Prototyping* yang diterapkan dikembangkan secara **Custom Prototyping (Evolutionary Prototype)** dengan 2 batasan spesifik:
1. **Batas Deployment:** Sistem **TIDAK melakukan tahap deployment penuh ke cloud server produksi / VPS berbayar**. Deployment beroperasi secara lokal (*local server execution*) memanfaatkan FastAPI + HTTP Webhook Ngrok tunnel untuk keperluan demonstrasi dan pengujian.
2. **Batas Iterasi Feedback:** Sistem **TIDAK menerapkan siklus iterasi umpan balik (*iterative user feedback loops*) yang berulang-ulang**. Evaluasi akhir dilakukan 1 kali pada pengujian *Black Box Testing*, pengujian *Retrieval Evaluation* (*Hit Rate & Precision*), dan pengujian *User Acceptance Testing (UAT/SUS)* pada sistem final.

Alasan Akademik:
- Menghindari tuntutan biaya server/VPS berbayar dan menjaga fokus penelitian pada domain informasi percetakan.
- Menghindari pelebaran ruang lingkup (*scope creep*) akibat saran masukan pengguna yang tidak berkesudahan.
- Memagari naskah Bab III dan Bab IV agar tidak dituntut proses deployment produksi oleh Dosen Penguji.

---

## DEC-014 — Perhitungan Harga Total Otomatis di WhatsApp via Direct LLM Contextual Calculation (CoT Prompting)
Status: LOCKED 🔒 (PERMANEN)

Keputusan:
Perhitungan harga total pesanan (seperti luas $P \times L \text{ m}^2$, cetak lembaran A3+, ID card, stiker, dan tier grosir) dieksekusi secara otomatis langsung di dalam teks percakapan WhatsApp menggunakan teknik **Direct Contextual Calculation via System Prompt Chain-of-Thought (CoT)**.

Pengalihan ke Web Portal Kalkulator (`bit.ly/harga-asia-visual`) resmi **dihilangkan dari naskah utama Bab I s.d. Bab V**.

Alasan Akademik & Teknis:
1. **Pemberdayaan Context Window Gemini 2.5 Flash:** Dokumen `04_daftar_estimasi_harga.txt` memuat 100% harga lengkap per m², lembar, pcs, dan rim beserta seluruh tier grosirnya.
2. **Deterministik Suhu 0.0:** Konfigurasi `temperature = 0.0` menjamin perkalian matematika berjalan secara konsisten tanpa variasi acak.
3. **Penyederhanaan Naskah Skripsi:** Menghilangkan keharusan mendokumentasikan antarmuka webview, CORS, dan JavaScript kalkulator di Bab III & Bab IV. Fokus naskah 100% pada Naive RAG WhatsApp Chatbot.

---

## DEC-015 — PENGUNCIAN FINAL PROJEK (CODE FREEZE 100% & SCOPE LOCK)
Status: LOCKED 🔒 (MUTLAK & PERMANEN)

Keputusan:
1. **Pengembangan Kode Dianggap Selesai (100% Done):** Seluruh fitur kodingan backend RAG (ChromaDB + Gemini 2.5 Flash + WhatsApp Fonnte + Conversational Condense Query + Direct Price Calculation) **DIKUNCI 100% TANPA PERUBAHAN LAGI**.
2. **Kebijakan Mini App & Ngrok:** Berkas kode Mini App dan konfigurasi Ngrok **TETAP DIPERTAHANKAN di folder projek (tidak dihapus)**, namun **DISEMBUNYIKAN dari naskah utama Bab I s.d. Bab V**.
3. **Fokus Naskah Utuh:** Naskah skripsi 100% murni dan fokus membahas **Chatbot Naive RAG WhatsApp (Fonnte)**. Fitur Mini App / Webview cukup dimasukkan di Bab VI sebagai "Saran Pengembangan Sistem di Masa Depan".

---

## DEC-016 — Finalisasi Penyempurnaan Sistem Chatbot RAG & Penutupan Pengembangan (Project Complete)
Status: LOCKED 🔒 (KESEPAKATAN MUTLAK & PROJEK SELESAI 100%)

Keputusan:
Sistem Chatbot RAG CV. Asia Visual Grafika secara resmi dinyatakan **SELESAI 100% DAN FINAL** per tanggal 28 September 2026. Seluruh perbaikan bug dan penyempurnaan knowledge base telah dituntaskan dengan kesepakatan teknis:

1. **Strategi Riwayat Percakapan (History-in-Prompt):**
   - Logika Query Condensing LLM resmi dihilangkan. Kueri asli pengguna selalu dikirim langsung ke ChromaDB tanpa distorsi kata.
   - Konteks multi-turn ditangani secara efisien dengan menyisipkan riwayat 2 giliran percakapan terakhir langsung ke dalam prompt LLM (`prompt_template.py`).
2. **Klarifikasi Otomatis (Underspecified Query & Clarification Dialogue):**
   - System Prompt mewajibkan bot melakukan klarifikasi sopan jika pengguna meminta perhitungan harga namun variabel penentu belum lengkap (misal: ukuran cm stiker, P×L spanduk, rangkap nota), mencegah halusinasi numerik.
3. **Penyempurnaan & Konsolidasi Knowledge Base (7 Dokumen Lengkap):**
   - `04_daftar_estimasi_harga.txt`: Penegasan label disambiguasi 18 seksi produk + tarif ongkos potong karter (A4/A3/A5/A6 Rp 10.000–25.000), laminating A3+, laminating meteran, dan mata ayam ekstra.
   - `06_estimasi_pcs_per_lembar_a3.txt`: Konsolidasi tabel komprehensif muat stiker A3+ untuk Kiss Cut (29×42 cm) dan Potong Manual (31×47 cm) dari 1×1 hingga 15×15 cm serta ukuran kustom.
   - `07_katalog_contoh_gambar_bahan.txt`: Katalog tautan foto sampel fisik bahan cetak & produk display berbasis teks alami yang terhubung langsung ke Google Drive / Cloud.
4. **Portal Admin Web (`/admin`):**
   - Manajemen Knowledge Base (CRUD), log chat global interaktif, dan pemantauan sistem dengan kredensial terproteksi.
5. **STATUS AKHIR PENGEMBANGAN TEKNIS:** **SELESAI 100% (PROJEK LENGKAP & TERSEGEL)**. Tidak ada lagi penambahan fitur atau pengubahan kode. Fokus kerja 100% dialihkan untuk penulisan naskah skripsi Bab I–VI.