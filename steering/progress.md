# PROGRESS LOG — Chatbot RAG Asia Visual Grafika
> 📌 File ini di-update otomatis setiap sesi diskusi oleh Agent.
> Terakhir diperbarui: 1 Oktober 2026

---

## CHECKLIST 48 TASK — BREAKDOWN LENGKAP

> Dibuat: 1 Oktober 2026 | Update status setiap sesi

### 🔴 PENGUJIAN (8 task)
- [x] Buat Google Forms dari instrumen SUS 10 pertanyaan
- [x] Sebarkan SUS ke 10–15 responden
- [ ] Kumpulkan & hitung skor SUS per responden
- [ ] Buat instrumen Human Evaluation (3 aspek: Relevansi, Kelengkapan, Kejelasan)
- [ ] Kirim Human Evaluation ke Mba Intan, Rizky, Shinta
- [ ] Kumpulkan & rekap hasil Human Evaluation ke tabel Word
- [ ] Perbaiki rata-rata tabel Retrieval di Word (sekarang 0.00 → HR=100%, P=0.567, Recall=100%)
- [ ] Tambahkan baris DeepSeek ke tabel Latensi & Token di Word

### 🔴 BAB I — PENDAHULUAN (6 task)
- [x] Tulis Identifikasi Masalah (2 poin — final, versi Dif + koreksi kecil) 🟢
- [x] Tulis Rumusan Masalah (2 poin — final) 🟢
- [ ] Tulis Batasan Masalah (cantumkan versi spesifik tiap tools) 🟡 *Draf siap, menunggu di-copy ke Word*
- [ ] Tulis Tujuan Penelitian
- [ ] Tulis Manfaat Penelitian (4 sub: Penulis, Universitas, Perusahaan, Masyarakat)
- [ ] Lengkapi Latar Belakang (tambah data WA, data empiris chat, justifikasi 3 model LLM) 🟢 *Draf lengkap 8 paragraf siap copy ke Word*

### 🔴 BAB II — LANDASAN TEORI (8 task)
- [ ] Tulis sub-bab FastAPI
- [ ] Tulis sub-bab ChromaDB
- [ ] Tulis sub-bab Gemini 2.5 Flash
- [ ] Tulis sub-bab HuggingFace Embedding (multilingual-e5-small)
- [ ] Tulis sub-bab CV. Asia Visual Grafika
- [ ] Isi tabel Literatur Sejenis — kolom Metode & Hasil (7 baris yang sudah ada judulnya)
- [ ] Tambah 8 judul penelitian sejenis lagi (total target 15 baris)
- [ ] Isi tabel Pembeda Literatur (semua kolom kosong)

### 🔴 BAB III — METODE PENELITIAN (7 task)
- [ ] Tulis isi Tahap Komunikasi (Prototyping) 🟡 *Draf selesai, menunggu di-copy ke Word*
- [ ] Tulis isi Perencanaan Cepat / Quick Planning
- [ ] Tulis isi Pemodelan Cepat / Quick Modelling
- [ ] Tulis isi Konstruksi
- [ ] Tulis isi Pengujian
- [ ] Buat diagram Alur Penelitian (Gambar 10)
- [ ] Buat diagram Arsitektur RAG (Gambar 11)

### 🔴 BAB IV — IMPLEMENTASI (9 task)
- [ ] Tulis Tahap Komunikasi
- [ ] Tulis Ruang Lingkup dan Batasan sistem
- [ ] Isi Tabel Knowledge Base (Tabel 6 — 7 baris untuk 7 file .txt)
- [ ] Buat/sisipkan diagram Use Case (Gambar 12)
- [ ] Buat/sisipkan diagram Activity
- [ ] Tulis Penyusunan Knowledge Base (jelaskan proses kurasi dari katalog & chat WA)
- [ ] Tulis Implementasi Alur RAG (chain.py, vectorstore.py, prompt_template.py)
- [ ] Tulis Pembuatan Antarmuka (screenshot WhatsApp + Portal Admin)
- [ ] Tulis Tahap Pengujian (prosedur pengujian)

### 🔴 BAB V — HASIL & PEMBAHASAN (8 task)
- [ ] Tulis analisis/pembahasan Tabel Black Box
- [ ] Tulis analisis/pembahasan Tabel Retrieval
- [ ] Tulis analisis/pembahasan Tabel Benchmark LLM
- [ ] Input data SUS ke tabel setelah responden masuk
- [ ] Tulis analisis/pembahasan SUS
- [ ] Input data Human Evaluation ke tabel
- [ ] Tulis analisis/pembahasan Human Evaluation
- [ ] Tulis Pembahasan keseluruhan

### 🔴 BAB VI — KESIMPULAN & SARAN (2 task)
- [ ] Tulis Kesimpulan (jumlah poin = jumlah Rumusan Masalah)
- [ ] Tulis Saran (6 poin dari batasan sistem)

---

## STATUS FASE SAAT INI
**FASE:** Pengujian + Penulisan Naskah (10 Hari)
**Hari ke:** 3 dari 10
**Deadline Mutlak Naskah:** 10 Oktober 2026
**Status Teknis:** 🔒 CODE FREEZE 100% (DEC-016) — Tidak ada kode baru

---

## AUDIT DOKUMEN WORD (REFISI SKRIPSI.docx) — 1 Oktober 2026

### BAB I — PENDAHULUAN
| Bagian | Status | Catatan |
|---|---|---|
| Latar Belakang | 🟡 Ada, perlu tambahan | Butuh: data WA, data empiris chat, justifikasi 3 model LLM, hapus bold judul di akhir |
| Identifikasi Masalah | 🔴 Kosong | Placeholder "Berdasarkan latar belakang..." belum diisi |
| Rumusan Masalah | 🔴 Kosong | Placeholder belum diisi. Catatan dosen: rumusan = implementasi saja |
| Batasan Masalah | 🔴 Kosong | Butuh versi spesifik tools |
| Tujuan Penelitian | 🔴 Kosong | |
| Manfaat Penelitian | 🔴 Kosong | 4 sub-bagian (Penulis, Universitas, Perusahaan, Masyarakat) |

### BAB II — LANDASAN TEORI
| Bagian | Status | Catatan |
|---|---|---|
| Chatbot | 🟢 Ada | Cukup lengkap |
| NLP (NLU & NLG) | 🟢 Ada | |
| Large Language Model | 🟢 Ada | Transformer sudah ada |
| Prompt Engineering | 🟢 Ada | |
| RAG | 🟡 Ada kerangka | Gambar ada, isi paragraf masih tipis |
| Vector Embedding | 🟡 Ada sebagian | |
| Prototyping | 🟢 Ada | |
| Python | 🟢 Ada | |
| OpenRouter | 🟢 Ada | |
| FastAPI | 🔴 Kosong | Sub-bab ada tapi tanpa isi |
| Gemini 2.5 Flash | 🔴 Kosong | Sub-bab ada tapi tanpa isi |
| HuggingFace Embedding | 🔴 Kosong | Sub-bab ada tapi tanpa isi |
| LangChain | 🟢 Ada | |
| ChromaDB | 🔴 Kosong | Sub-bab ada tapi tanpa isi |
| CV. Asia Visual Grafika | 🔴 Kosong | |
| Tabel Literatur Sejenis | 🔴 Kosong | 7 dari 15 judul terisi, semua kolom isi masih kosong |
| Tabel Pembeda Literatur | 🔴 Kosong | Semua sel kosong |

### BAB III — METODOLOGI PENELITIAN
| Bagian | Status | Catatan |
|---|---|---|
| Alur Penelitian | 🟡 Ada gambar placeholder | Gambar 10 belum ada |
| Wawancara | 🟢 Ada | Tabel teknis wawancara sudah ada |
| Observasi | 🟢 Ada | |
| Studi Dokumen | 🟢 Ada | |
| Studi Literatur | 🟢 Ada | |
| Metode Pengembangan (5 tahap Prototyping) | 🔴 Kosong | Judul ada, semua isi kosong |

### BAB IV — IMPLEMENTASI
| Bagian | Status | Catatan |
|---|---|---|
| Tahap Komunikasi | 🔴 Kosong | |
| Perencanaan Cepat (Ruang Lingkup) | 🔴 Kosong | |
| Analisis Kebutuhan Fungsional | 🟢 Ada | 4 poin sudah ada |
| Tabel Kebutuhan Perangkat | 🟢 Ada | 11 komponen sudah ada |
| Perancangan Knowledge Base | 🔴 Kosong | Tabel 6 kosong |
| Perancangan Alur RAG | 🟡 Ada gambar placeholder | Gambar 11 belum ada |
| Perancangan Alur Chatbot | 🔴 Kosong | |
| Use Case Diagram | 🟡 Ada gambar placeholder | Gambar 12 belum ada |
| Activity Diagram | 🔴 Kosong | |
| Penyusunan Knowledge Base | 🔴 Kosong | |
| Implementasi Alur RAG | 🔴 Kosong | |
| Pembuatan Antarmuka | 🔴 Kosong | |
| Tahap Pengujian | 🔴 Kosong | |

### BAB V — HASIL DAN PEMBAHASAN
| Bagian | Status | Catatan |
|---|---|---|
| Tabel Black Box (10 skenario) | 🟢 Ada | Semua "Sesuai" — sudah bisa dipakai |
| Tabel Akurasi Retrieval | 🟡 Ada data, ada bug | Rata-rata masih 0.00 — perlu dihitung: Rata HR=100%, P=0.567, Recall=100% |
| Tabel Latensi LLM | 🟡 Ada, tapi tidak lengkap | Hanya 2 model (Gemini + GPT-4o-mini). DeepSeek belum ada di Word |
| Tabel Token Usage | 🟡 Ada, tidak lengkap | Sama, hanya 2 model |
| Tabel SUS | 🔴 Kosong | Belum ada responden |
| Tabel Human Evaluation | 🔴 Kosong | 3 responden toko (Mba Intan, Rizky, Shinta) belum mengisi |
| Pembahasan | 🔴 Kosong | Belum ada satu kalimat pun |

### BAB VI — KESIMPULAN & SARAN
| Bagian | Status | Catatan |
|---|---|---|
| Kesimpulan | 🔴 Kosong | Harus menjawab sejumlah rumusan masalah |
| Saran | 🔴 Kosong | |

---

## BLOCKER UTAMA (Harus diselesaikan sekarang)

1. 🟡 ~~Bug rata-rata tabel retrieval = 0.00~~ → Masih perlu diisi manual di Word: HR=100%, P=0.567, Recall=100%
2. ✅ ~~SUS belum disebar~~ → Google Forms sudah dibuat & disebar
3. 🔴 **Human Evaluation belum dibuat** → Instrumen belum ada, kirim ke Mba Intan, Rizky, Shinta
4. 🔴 **Rumusan Masalah kosong** → Kunci semua bab lain, harus dirumuskan segera
5. 🔴 **DeepSeek belum ada di tabel Word** → Tambahkan dari data testing
6. 🔴 **Diagram-diagram Bab III & IV belum dibuat** → Use Case, Activity, Arsitektur RAG

---

## DATA PENGUJIAN YANG SUDAH ADA & SIAP PAKAI

### Akurasi Retrieval (dari testing/tabel_akurasi_retrieval.csv)
- Hit Rate@3 = **100%** | Precision@3 = **0.567** | Recall@3 = **100%**
- 10 pertanyaan uji, semua Hit = 1

### Benchmark LLM (dari testing/ringkasan_evaluasi.txt)
| Model | Latensi Rata-rata | Total Token |
|---|---|---|
| google/gemini-2.5-flash | **1.645 detik** | 2.095 |
| openai/gpt-4o-mini | 2.808 detik | 2.019 |
| deepseek/deepseek-v4-flash-0731 | 11.069 detik | 2.692 |

---

## RENCANA AKSI PRIORITAS (Sisa 7 Hari)

| Hari | Tanggal | Target Output |
|---|---|---|
| H3 | 1 Okt | ✅ Audit selesai — Buat instrumen SUS, sebarkan |
| H4 | 2 Okt | Rumusan Masalah + Identifikasi + Tujuan Bab I |
| H5 | 3 Okt | Isi Tabel Literatur + sub-bab kosong Bab II |
| H6 | 4 Okt | Isi 5 tahap Prototyping Bab III + Diagram-diagram |
| H7 | 5 Okt | Bab IV lengkap (KB, RAG, Antarmuka) |
| H8 | 6 Okt | Bab V lengkap (input data SUS + Human Eval + pembahasan) |
| H9 | 7 Okt | Bab VI Kesimpulan & Saran |
| H10 | 8-9 Okt | Review format, cek 80 halaman, siap bimbingan |

---

## LOG SESI DISKUSI

### Sesi 2 Oktober 2026 (Sesi 6) — Hari ke-4 dari 10
**Topik:** Revisi Identifikasi Masalah versi Dif

**Output Konkret:**
- Dif menulis ulang 2 poin identifikasi masalah dengan kata-katanya sendiri — lebih natural & kontekstual
- Koreksi kecil diberikan: "Belum adanya" → "Belum tersedianya", "relevan" → "efisien", tambah istilah Inggris italic
- Versi final siap copy ke Word

**Status Berubah:**
- Identifikasi Masalah: sudah 🟢 dari sesi sebelumnya, versi diperbarui ke versi Dif

**Tindak Lanjut (untuk Dif):**
- Copy identifikasi masalah versi Dif (+ koreksi kecil) ke Word
- Lanjut sesi berikutnya: Tujuan Penelitian & Manfaat Penelitian

---

### Sesi 2 Oktober 2026 (Sesi 5) — Hari ke-4 dari 10
**Topik:** Bab I — Identifikasi Masalah & Rumusan Masalah final

**Output Konkret:**
- Identifikasi Masalah 2 poin final siap copy ke Word
- Rumusan Masalah 2 poin final siap copy ke Word
- Kerangka Kesimpulan Bab VI (template dengan placeholder) sudah dibuat

**Status Berubah:**
- Bab I — Identifikasi Masalah: 🔴 Kosong → 🟢 Final siap copy ke Word
- Bab I — Rumusan Masalah: 🔴 Kosong → 🟢 Final siap copy ke Word
- Bab VI — Kesimpulan: 🔴 Kosong → 🟡 Kerangka ada, menunggu data SUS & Human Eval

**Tindak Lanjut (untuk Dif):**
- Copy Identifikasi + Rumusan ke Word sekarang
- Lanjut sesi berikutnya: Tujuan Penelitian & Manfaat Penelitian Bab I

---

### Sesi 2 Oktober 2026 (Sesi 4) — Hari ke-4 dari 10
**Topik:** Finalisasi kata pembuka rumusan masalah & konfirmasi 2 rumusan

**Output Konkret:**
- 2 rumusan masalah DIKUNCI — Dif setuju opsi 2 rumusan
- Kata pembuka disepakati: Rumusan 1 = "Seberapa baik", Rumusan 2 = "Manakah"
- Draft 2 kalimat rumusan masalah sudah dibuat, menunggu konfirmasi final Dif

**Status Berubah:**
- Jumlah rumusan masalah: 🟡 Belum ditentukan → 🟢 DIKUNCI = 2 rumusan
- Rumusan Masalah: 🔴 Kosong → 🟡 Draft 2 kalimat siap, menunggu konfirmasi

**Tindak Lanjut (untuk Dif):**
- Konfirmasi setuju kalimat 2 rumusan di atas
- Setelah iya, minta tulis Identifikasi + Rumusan + Kesimpulan sekaligus

---

### Sesi 2 Oktober 2026 (Sesi 3) — Hari ke-4 dari 10
**Topik:** Diskusi pengurangan metrik & jumlah rumusan masalah

**Output Konkret:**
- Opsi 2 rumusan masalah diusulkan (lebih aman):
  1. Fungsionalitas → Black Box + SUS
  2. Kinerja LLM → Latency + Token + Human Eval
- Akurasi retrieval diusulkan masuk sebagai bagian pembahasan Rumusan 1, bukan rumusan tersendiri
- Belum ada keputusan final — menunggu konfirmasi Dif (pilih 2 atau 3)

**Status Berubah:**
- Tidak ada status yang berubah — menunggu keputusan Dif

**Tindak Lanjut (untuk Dif):**
- Tentukan pilihan: 2 rumusan (lebih aman) atau 3 rumusan (lebih lengkap)
- Setelah sepakat, minta kalimat formal langsung

---

### Sesi 2 Oktober 2026 (Sesi 2) — Hari ke-4 dari 10
**Topik:** Finalisasi struktur Identifikasi Masalah & Rumusan Masalah

**Output Konkret:**
- Struktur 3 poin Identifikasi + Rumusan + Kesimpulan disepakati:
  1. Fungsionalitas chatbot → Black Box + SUS
  2. Kinerja LLM (latency, token, Human Eval) → 3 model dibandingkan
  3. Akurasi retrieval (Hit Rate & Precision) → angka sudah ada
- Pola linear identifikasi → rumusan → kesimpulan dikunci mengikuti contoh skripsi temannya
- Rumusan ke-3 diganti dari Black Box (lemah) ke akurasi retrieval (lebih kuat, ada datanya)

**Status Berubah:**
- Kerangka Identifikasi & Rumusan Masalah: 🔴 Kosong → 🟡 Struktur disepakati, menunggu kalimat formal

**Tindak Lanjut (untuk Dif):**
- Konfirmasi setuju → minta kalimat formal siap copy ke Word

---

### Sesi 2 Oktober 2026 (Sesi 1) — Hari ke-4 dari 10
**Topik:** Analisis identifikasi masalah & rumusan masalah vs 3 kriteria

**Output Konkret:**
- Evaluasi 4 identifikasi masalah dari kerangka asli → poin 4 perlu diubah framing
- Evaluasi 3 rumusan masalah → rumusan 3 (Black Box) terlalu lemah, direkomendasikan dibuang
- Rekomendasi final: 3 identifikasi masalah + 2 rumusan masalah
- Research gap diidentifikasi dari tabel literatur sejenis yang sudah ada: sektor UMKM percetakan, multi-model LLM, platform WhatsApp

**Status Berubah:**
- Tidak ada teks naskah yang selesai — sesi ini analisis & rekomendasi

**Tindak Lanjut (untuk Dif):**
- Konfirmasi apakah setuju dengan 2 rumusan masalah yang direkomendasikan
- Setelah sepakat, minta draf kalimat formal Identifikasi Masalah + Rumusan Masalah

---

### Sesi 1 Oktober 2026 (Sesi 13) — Hari ke-3 dari 10
**Topik:** Pemulihan progress.md versi lama dari git history

**Output Konkret:**
- File `KERANGKA_BERPIKIR_ASLI.md` dibuat — berisi narasi asli Dif dari git commit 36a602a1
- Dipulihkan: rencana LB (16 poin), identifikasi masalah, rumusan masalah, kerangka Bab 3-6, catatan dosen

**Status Berubah:**
- `KERANGKA_BERPIKIR_ASLI.md`: 🔴 Hilang → 🟢 Dipulihkan

**Tindak Lanjut (untuk Dif):**
- Baca `KERANGKA_BERPIKIR_ASLI.md` — terutama bagian catatan bingung Bab 3 (data primer vs sekunder)
- Lanjut diskusi untuk menjawab kebingungan tersebut sebelum nulis Bab 3

---

### Sesi 1 Oktober 2026 (Sesi 12) — Hari ke-3 dari 10
**Topik:** Bab I — Draf Latar Belakang lengkap

**Output Konkret:**
- Draf Latar Belakang lengkap 8 paragraf selesai, siap copy ke Word
- Mencakup semua 11 poin dari rencana alur di progress.md
- Paragraf 1: Tren digital printing 3.39%
- Paragraf 2: Migrasi komunikasi + WhatsApp
- Paragraf 3: Profil Asia Visual + masalah operasional (wawancara Mas Aji & Rizky)
- Paragraf 4: Bukti empiris 4.052 sesi WA, sampel 500
- Paragraf 5: Solusi chatbot WA + kelemahan rule-based
- Paragraf 6: Pengenalan RAG + justifikasi vs LLM biasa
- Paragraf 7: Justifikasi 3 model LLM via OpenRouter (Gemini, GPT-4o-Mini, DeepSeek)
- Paragraf 8: Penutup → judul penelitian + 4 metode pengujian

**Status Berubah:**
- Bab I — Latar Belakang: 🟡 Ada sebagian → 🟢 Draf lengkap siap copy ke Word

**Tindak Lanjut (untuk Dif):**
- Copy draf latar belakang ke Word, gantikan teks lama
- Lanjut sesi berikutnya: Identifikasi Masalah Bab I

---

### Sesi 1 Oktober 2026 (Sesi 11) — Hari ke-3 dari 10
**Topik:** Analisis gap Latar Belakang Bab I

**Output Konkret:**
- Identifikasi 5 poin yang BELUM ada di Word tapi ada di rencana progress.md:
  1. Data empiris 4.052 sesi WA (sampel 500) — PALING PENTING
  2. Profil & masalah Asia Visual dari wawancara Mas Aji & Rizky
  3. Justifikasi 3 model LLM + OpenRouter
  4. Justifikasi WhatsApp sebagai platform
  5. Perbaikan penutup latar belakang (hapus bold judul)
- Urutan penempatan 5 poin di dalam teks sudah ditentukan

**Status Berubah:**
- Tidak ada status yang berubah — sesi ini analisis gap, belum ada teks ditulis

**Tindak Lanjut (untuk Dif):**
- Minta draf paragraf untuk salah satu dari 5 poin di atas
- Prioritas pertama: data empiris 4.052 sesi WA (paling kuat sebagai bukti)

---

### Sesi 1 Oktober 2026 (Sesi 10) — Hari ke-3 dari 10
**Topik:** Bab I — Batasan Masalah bagian Metode

**Output Konkret:**
- Draf 3 poin Batasan Masalah bagian Metode selesai, siap copy ke Word
- Urutan pengumpulan data dikonfirmasi: Wawancara → Observasi → Studi Dokumen → Studi Literatur
- Poin c (pembatasan scope: bukan sistem transaksi/pembayaran) ditambahkan untuk memagari dari tuntutan penguji

**Status Berubah:**
- Bab I — Batasan Masalah (Metode): 🔴 Kosong → 🟡 Draf siap (menunggu di-copy ke Word)

**Tindak Lanjut (untuk Dif):**
- Copy 3 poin metode ke Word
- Lanjut sesi berikutnya: Batasan Proses, lalu Identifikasi Masalah

---

### Sesi 1 Oktober 2026 (Sesi 9) — Hari ke-3 dari 10
**Topik:** Bab I — Susun kalimat final Batasan Alat

**Output Konkret:**
- Kalimat batasan alat (9 poin) final siap copy-paste ke Word
- Sudah dikoreksi: nama embedding, versi FastAPI, pembagian model LLM (utama vs benchmark)
- Mencakup: Python, WhatsApp, Fonnte, FastAPI, LangChain, ChromaDB, Embedding, LLM, Ngrok

**Status Berubah:**
- Bab I — Batasan Masalah (Alat): 🟡 Draf awal → 🟢 Final siap copy ke Word

**Tindak Lanjut (untuk Dif):**
- Copy 9 poin batasan alat ke Word
- Lanjut sesi berikutnya: Identifikasi Masalah atau Rumusan Masalah Bab I

---

### Sesi 1 Oktober 2026 (Sesi 8) — Hari ke-3 dari 10
**Topik:** Verifikasi & koreksi batasan alat Bab I

**Output Konkret:**
- Koreksi 3 item batasan alat dari versi yang Dif tulis:
  - Embedding: `intfloat-multilinggual-e5` → `intfloat/multilingual-e5-small`
  - FastAPI: `0.11` → `0.111.0` (dikonfirmasi dari requirements.txt)
  - LLM: Gemini = sistem utama; GPT-4o-Mini & DeepSeek = benchmark saja
- Versi yang dikonfirmasi dari requirements.txt: FastAPI 0.111.0, ChromaDB 0.5.3, LangChain 0.2.5, Ngrok 3.39.2, Python 3.10.0

**Status Berubah:**
- Tidak ada status sub-bab yang berubah — sesi ini verifikasi data

**Tindak Lanjut (untuk Dif):**
- Perbaiki batasan alat di Word sesuai koreksi di atas
- Tambahkan LangChain 0.2.5 dan Fonnte ke tabel batasan alat
- Lanjut sesi berikutnya: susun kalimat batasan alat final atau lanjut Identifikasi/Rumusan Masalah

---

### Sesi 1 Oktober 2026 (Sesi 7) — Hari ke-3 dari 10
**Topik:** Bab I — Batasan Masalah (Metode, Alat, Proses)

**Output Konkret:**
- Draf Batasan Masalah lengkap (3 sub-bagian: Metode, Alat, Proses) siap copy-paste ke Word
- Tabel 11 alat dengan versi spesifik sudah lengkap
- 5 poin proses pengujian sudah terdokumentasi

**Status Berubah:**
- Bab I — Batasan Masalah: 🔴 Kosong → 🟡 Draf siap (menunggu Dif copy ke Word)

**Tindak Lanjut (untuk Dif):**
- Copy Batasan Masalah ke Word
- Lanjut sesi berikutnya: Identifikasi Masalah atau Rumusan Masalah Bab I

---

### Sesi 1 Oktober 2026 (Sesi 6) — Hari ke-3 dari 10
**Topik:** Membuat file pemahaman sistem untuk Dif

**Output Konkret:**
- File `PEMAHAMAN_SISTEM.md` dibuat — rangkuman lengkap sistem dalam bahasa sederhana
- Mencakup: konfigurasi parameter, arsitektur, alur data 14 langkah, strategi khusus (History-in-Prompt, CoT, Greeting, Menu 1-4), integrasi Fonnte, 7 KB, komponen, dan ringkasan jawaban sidang

**Status Berubah:**
- `PEMAHAMAN_SISTEM.md`: 🔴 Belum ada → 🟢 Selesai dibuat

**Tindak Lanjut (untuk Dif):**
- Baca `PEMAHAMAN_SISTEM.md` sampai selesai
- Coba jawab 5 pertanyaan sidang di bagian 10 dengan kata-katamu sendiri
- Lanjut ke penulisan Bab III atau Bab IV

---

### Sesi 1 Oktober 2026 (Sesi 5) — Hari ke-3 dari 10
**Topik:** Mulai penulisan Bab III — Tahap Komunikasi

**Output Konkret:**
- Draf teks Tahap Komunikasi (Prototyping) selesai — siap copy-paste ke Word
- Mencakup: wawancara Mas Aji (6 April 2026), observasi 4.052 sesi chat WA, sampel 500 sesi
- Rujukan: Mulyani (2017) & Sugiyono (2017)

**Status Berubah:**
- Bab III — Tahap Komunikasi: 🔴 Kosong → 🟡 Draf siap (menunggu Dif copy ke Word)

**Tindak Lanjut (untuk Dif):**
- Copy teks Tahap Komunikasi ke Word
- Lanjut sesi berikutnya: Tahap Perencanaan Cepat (Quick Planning) Bab III

---

### Sesi 1 Oktober 2026 (Sesi 4) — Hari ke-3 dari 10
**Topik:** Update status SUS + perencanaan langkah berikutnya

**Output Konkret:**
- Dif sudah membuat Google Forms SUS dan menyebarkannya ke responden
- Checklist SUS di progress.md diperbarui (2 task selesai)

**Status Berubah:**
- Google Forms SUS: 🔴 Belum ada → 🟢 Sudah dibuat & disebar
- SUS di THESIS_STATE: 🟡 Instrumen selesai → 🟡 Menunggu responden masuk

**Tindak Lanjut (untuk Dif):**
- Buat instrumen Human Evaluation untuk Mba Intan, Rizky, Shinta (10 menit)
- Lanjut tulis Bab I: Identifikasi Masalah + Rumusan Masalah

---

### Sesi 1 Oktober 2026 (Sesi 3) — Hari ke-3 dari 10
**Topik:** Breakdown semua task yang belum selesai

**Output Konkret:**
- Breakdown lengkap 48 task terbagi 7 kategori (Pengujian, Bab I–VI)
- Setiap task sudah spesifik dan bisa langsung dikerjakan

**Status Berubah:**
- Tidak ada status sub-bab yang berubah — ini sesi perencanaan

**Tindak Lanjut (untuk Dif):**
- Buat Google Forms SUS hari ini dan sebarkan
- Lanjut sesi berikutnya: buat Human Evaluation, lalu mulai tulis Bab I

---

### Sesi 1 Oktober 2026 (Sesi 2) — Hari ke-3 dari 10
**Topik:** Pembuatan instrumen kuesioner SUS

**Output Konkret:**
- Instrumen SUS 10 pertanyaan baku sudah dibuat (bahasa Indonesia, konteks chatbot WA Asia Visual)
- Teks pengantar form sudah dibuat (siap copy ke Google Forms)
- Bagian data responden (nama, usia, pekerjaan, pengalaman chatbot) sudah dibuat
- Rumus hitung skor SUS (ganjil: nilai−1, genap: 5−nilai, ×2.5) sudah didokumentasikan
- Tabel skala interpretasi SUS (Bangor et al. 2008 & Brooke 1996) sudah siap untuk naskah

**Status Berubah:**
- Instrumen SUS: 🔴 Belum ada → 🟢 Siap, tinggal buat di Google Forms dan disebar

**Tindak Lanjut (untuk Dif):**
- Buat Google Forms dari 10 pertanyaan SUS di atas (skala linear 1–5 per pertanyaan)
- Sebarkan ke 10–15 orang segera (teman kuliah, rekan, pelanggan Asia yang dikenal)
- Lanjut sesi berikutnya: buat instrumen Human Evaluation untuk Mba Intan, Rizky, Shinta

---

### Sesi 1 Oktober 2026 — Hari ke-3 dari 10
**Topik:** Setup sistem progress tracking + Audit dokumen Word

**Output Konkret:**
- Membaca & merangkum seluruh projek (backend, KB, testing, konfigurasi)
- Audit menyeluruh dokumen `REFISI SKRIPSI.docx` — setiap sub-bab dicek status nyatanya
- Memperbarui `progress.md` dengan tabel audit lengkap per sub-bab
- Memperbarui `steering/02_THESIS_STATE.md` dengan status nyata dari Word
- Membuat `steering/07_PROGRESS_UPDATE_PROTOCOL.md` — aturan auto-update progress
- Membuat hook `Stop` di `.kiro/hooks/update-progress-on-stop.json` — agent otomatis update di akhir sesi

**Status Berubah:**
- `progress.md`: kosong/tidak terstruktur → 🟢 Terstruktur penuh dengan audit + log
- `steering/02_THESIS_STATE.md`: estimasi lama → 🟢 Diperbarui dengan kondisi nyata dokumen Word
- `steering/07_PROGRESS_UPDATE_PROTOCOL.md`: 🔴 Belum ada → 🟢 Dibuat
- Hook auto-update: 🔴 Belum ada → 🟢 Aktif

**Tindak Lanjut (untuk Dif):**
- Segera buat & sebarkan instrumen SUS (10 pertanyaan) ke 10–15 orang → ini blocker Bab V
- Kirim Human Evaluation ke Mba Intan, Rizky, Shinta
- Lanjut ke sesi berikutnya: isi Rumusan Masalah + Identifikasi Masalah Bab I

---

## CATATAN HISTORIS (dari progress.md lama)

### Rencana Alur Bab I (Latar Belakang)
- Kenaikan tren usaha digital printing (data MIX Marcomm 2026: +3.39%)
- Migrasi komunikasi offline → online via chat
- Keunggulan WhatsApp sebagai sarana UMKM
- Profil Asia Visual (dari wawancara Mas Aji)
- Meningkatnya pelanggan online, beban setter (dari wawancara Rizky)
- Bukti empiris: observasi data chat WhatsApp 2025 (4.052 sesi, sampel 500)
- Solusi chatbot WhatsApp otomatisasi informasi
- Karakteristik pelanggan (variasi bahasa) → kelemahan chatbot konvensional
- Pengenalan RAG dari penelitian lain
- RAG butuh LLM → OpenRouter → 3 model low-cost UMKM
- Kesimpulan: implementasi + pengujian (Hit Rate, Precision, SUS, Human Eval)

### Catatan Dosen Penguji
- Bu Viva: hadir Selasa jam 8-9, sisanya zoom
- Bu Faiz: revisi pakai notulensi, bagian dikerjakan dilabeli kuning

### Identifikasi Masalah (rencana)
1. Belum ada pemusatan informasi di Asia Visual (serba manual)
2. Belum ada otomatisasi virtual asisten 24/7 (beban setter)
3. Chatbot kata kunci (rule-based) lemah terhadap variasi bahasa pelanggan
4. LLM gratis seringkali kurang akurat → perlu LLM low-cost terbaik dari OpenRouter

### Saran Bab VI (rencana)
- CRUD knowledge base lebih modern (tidak perlu edit .txt manual)
- Perkuat keamanan autentikasi file KB
- GraphRAG untuk konsistensi harga
- Kemampuan analisis gambar (multimodal RAG)
- Dukungan bahasa asing
- Peningkatan akurasi retrieval (tidak ambigu)


# latar belakang 
Berikut latar belakang terbaru dalam bentuk narasi utuh. Isinya mengikuti keputusan terakhir: layanan informasi saja, satu model LLM, tanpa perbandingan model, dan pengujian *retrieval*, *Human Evaluation*, serta SUS. Tanda **[...]** adalah data atau sitasi yang harus diisi dari sumber asli.

---

**1.1 Latar Belakang**

Industri media kreatif, seperti percetakan digital (*digital printing*), berperan penting dalam perekonomian nasional seiring kemajuan teknologi, perubahan pasar, dan minat konsumen. Sektor percetakan digital mengalami pertumbuhan yang stabil, dengan proyeksi kenaikan sekitar 3,39% pada tahun 2026 yang menunjukkan tingkat konsumsi masyarakat yang terus berkembang dan menjangkau berbagai lapisan (MIX Marcomm, 2026). Dibandingkan dengan percetakan *offset* konvensional, *digital printing* semakin diminati karena prosesnya lebih cepat, tidak memerlukan pembuatan plat, dan cocok untuk pesanan dalam jumlah kecil **(sitasi)**. Pada tahun **[tahun terbaru]**, produksi cetak nasional tercatat **[data kenaikan produksi cetak]** **(sitasi)**. Perkembangan sektor ini didorong oleh ketergantungan berbagai sektor lain, antara lain usaha mikro, kecil, dan menengah (UMKM), instansi perkantoran, dan institusi pendidikan (Rismayanti et al., 2025). Pada segmen ini, permintaan terbesar berasal dari media promosi luar ruangan seperti banner dan spanduk untuk publikasi acara, label stiker, serta produk merchandise untuk keperluan *branding*. Kondisi tersebut menuntut pelaku usaha untuk tidak hanya mengandalkan kesiapan produksi, tetapi juga menyediakan akses informasi yang praktis bagi pelanggan.

Di era digitalisasi, komunikasi antara pelaku usaha dan konsumen beralih dari interaksi langsung ke berbagai platform daring (Kotler et al., 2021). Perubahan ini turut mengubah cara konsumen menyampaikan pertanyaan dan memperoleh informasi tentang produk maupun layanan, termasuk proses pemesanan yang bergeser dari kunjungan langsung ke toko menjadi pemesanan melalui percakapan daring. Dibandingkan dengan situs web dan media daring lainnya, aplikasi percakapan menjadi salah satu media yang paling banyak digunakan sebagai sarana komunikasi (Yoshio, 2022). Di Indonesia, WhatsApp hampir selalu digunakan pelaku UMKM untuk menerima pesanan dan berkonsultasi dengan pelanggan karena mudah diakses, familier bagi hampir semua kalangan, dan tidak memerlukan instalasi tambahan **(sitasi)**. Fitur WhatsApp Business, seperti katalog produk dan balasan otomatis, juga membantu usaha kecil mengelola komunikasi tanpa investasi besar **(sitasi)**.

Pergeseran tersebut juga dialami oleh Asia Visual, usaha *digital printing* di **[lokasi]** yang berdiri sejak **[tahun]** dan melayani **[jenis produk]** untuk pelanggan perorangan, UMKM, dan institusi **(wawancara dengan Mas Aji, [tanggal])**. Berdasarkan wawancara dengan Rizky selaku admin, jumlah pelanggan yang memesan secara daring terus meningkat dan kini melampaui pelanggan yang datang langsung, yaitu sekitar **[X%]** berbanding **[Y%]** pada **[periode]**. Peningkatan ini menambah beban kerja admin karena informasi mengenai bahan, tata cara penyiapan berkas desain, dan estimasi biaya belum terpusat dan belum terotomatisasi selama 24 jam. Setiap pertanyaan harus dijawab secara manual, sehingga pelanggan yang menghubungi di luar jam kerja baru terlayani pada hari berikutnya **(wawancara dengan Rizky, [tanggal])**.

Hasil observasi terhadap data percakapan WhatsApp Asia Visual tahun 2025 menunjukkan bahwa pelanggan cenderung menanyakan hal-hal yang sama. Dari **[jumlah]** percakapan yang dianalisis, pertanyaan dikelompokkan ke dalam kategori **[misalnya: jenis bahan dan produk, ketentuan berkas desain, estimasi biaya, waktu pengerjaan, prosedur pemesanan]**, dengan kategori terbanyak adalah **[kategori]** sebesar **[X%]**. Pola ini menunjukkan bahwa kebutuhan informasi pelanggan cukup terstruktur sehingga berpotensi diotomatisasi. Chatbot WhatsApp dapat menjawab pertanyaan secara otomatis selama 24 jam, menjadi pusat informasi yang selama ini belum terdokumentasi, dan meningkatkan efisiensi admin dalam menjawab pertanyaan yang berulang.

Meski demikian, pelanggan Asia Visual menyampaikan pertanyaan dengan variasi bahasa yang sangat beragam. Data percakapan memperlihatkan penggunaan bahasa informal, singkatan, salah ketik, campuran bahasa daerah, dan susunan kalimat yang tidak baku, misalnya **[contoh nyata dari data chat]**. Chatbot konvensional berbasis aturan (*rule-based*) bekerja dengan mencocokkan kata kunci pada kamus (*dictionary*) yang ditulis manual. Pendekatan ini rapuh terhadap variasi tersebut karena setiap kemungkinan penulisan harus didaftarkan terlebih dahulu. Pertanyaan yang tidak cocok dengan kata kunci gagal dijawab, dan pemeliharaan kamus semakin berat ketika produk atau harga berubah **(sitasi)**. Chatbot berbasis kecerdasan buatan (*Artificial Intelligence*/AI) tidak memiliki keterbatasan ini karena mampu memahami bahasa alami tanpa perlu dijadikan kamus **(sitasi)**. Pendekatan yang umum digunakan meliputi *Large Language Model* (LLM), *fine-tuning*, dan *Retrieval-Augmented Generation* (RAG) **(sitasi)**. Namun, pada konteks usaha spesifik seperti percetakan digital, LLM yang digunakan tanpa sumber informasi pendukung sering memberikan jawaban yang meleset (halusinasi), misalnya harga, ketersediaan bahan, atau ketentuan berkas yang tidak sesuai dengan kondisi usaha, sehingga berpotensi menyesatkan pelanggan **(sitasi)**.

RAG mengatasi masalah tersebut dengan mencari potongan informasi yang relevan dari basis pengetahuan berdasarkan makna pertanyaan, bukan kesamaan kata kunci, lalu menyertakannya sebagai konteks bagi LLM untuk menyusun jawaban **(Lewis et al., 2020)**. Dengan demikian, jawaban berpijak pada dokumen milik usaha dan risiko halusinasi berkurang. Basis pengetahuan juga dapat diperbarui tanpa melatih ulang model, tidak seperti *fine-tuning* yang membutuhkan data dan sumber daya komputasi lebih besar **(sitasi)**. Efektivitas RAG telah dibuktikan pada berbagai sektor, misalnya **[pendidikan, kesehatan, layanan pelanggan, hukum]**, dengan hasil **[ringkasan temuan tiap penelitian]** **(sitasi penelitian terdahulu)**. Namun, penelitian tersebut belum menyentuh layanan informasi UMKM *digital printing* dengan karakteristik bahasa pelanggan seperti di atas **[validasi lewat pencarian literatur]**.

Penerapan RAG membutuhkan LLM sebagai generator jawaban. Salah satu cara mengaksesnya adalah melalui OpenRouter, platform yang menyediakan banyak model dari berbagai vendor melalui satu API, termasuk beberapa model gratis **(OpenRouter, 2026)**. Namun, model gratis memiliki keterbatasan, yaitu kemampuan meringkas dan menangkap informasi dari konteks yang kurang baik, kualitas respons yang tidak konsisten, serta batas penggunaan yang ketat **(sitasi/observasi awal)**. Kondisi ini kurang sesuai bagi layanan pelanggan yang menuntut jawaban akurat dan stabil. Oleh karena itu, penelitian ini menggunakan satu model berbayar berbiaya rendah, yaitu **[nama model]**, agar tetap terjangkau bagi UMKM namun cukup andal menyusun jawaban dari konteks yang diberikan **(alasan pemilihan, mis. biaya per token dan kemampuan model, sitasi)**.

Chatbot yang dikembangkan difokuskan sebagai layanan informasi, yaitu menjawab pertanyaan seputar jenis bahan dan produk, panduan penyiapan berkas desain, dan estimasi biaya cetak. Sistem tidak memproses pembayaran, tidak menerima atau mengelola berkas desain pelanggan, dan tidak menangani transaksi pemesanan. Pemrosesan tersebut tetap dilakukan oleh admin Asia Visual, sehingga chatbot berperan mengurangi pertanyaan repetitif tanpa menggantikan proses transaksi.

Berdasarkan uraian tersebut, penelitian ini mengimplementasikan chatbot WhatsApp berbasis RAG sebagai layanan informasi *digital printing* pada Asia Visual, kemudian menguji apakah sistem berjalan dengan baik. Pengujian dilakukan pada tiga aspek. Pertama, kinerja *retrieval* diukur dengan *Hit Rate* dan *Precision* (dengan *Recall* sebagai pertimbangan tambahan) untuk memastikan informasi yang diambil relevan terhadap pertanyaan pelanggan. Kedua, kualitas jawaban dinilai melalui *Human Evaluation* oleh pihak toko. Ketiga, kebergunaan sistem dinilai menggunakan *System Usability Scale* (SUS) oleh pengguna awam. Hasil pengujian digunakan untuk menyimpulkan kelayakan chatbot sebagai layanan informasi bagi UMKM Asia Visual.

---

Catatan:
- Kalimat gap di paragraf RAG ("belum menyentuh layanan informasi UMKM *digital printing*") hanya boleh dipertahankan jika sudah dibuktikan lewat tabel penelitian terdahulu di Bab 2.
- Paragraf ruang lingkup bisa dipindah ke subbab Batasan Masalah jika dosen ingin latar belakang lebih ringkas.
- Istilah di paragraf terakhir (*retrieval*, *Human Evaluation*, SUS, "berjalan dengan baik") harus konsisten dengan rumusan masalah, tujuan, dan kesimpulan.

Mau saya lanjutkan dengan identifikasi masalah, rumusan, batasan, dan tujuan dalam kalimat final yang selaras dengan latar belakang ini?



Dengan satu rumusan, **"Seberapa baik"** adalah pilihan paling tepat karena jawabannya berupa angka dan penilaian yang tegas. Implementasi dan penyusunan knowledge base tidak hilang, tetapi dipindah ke tujuan dan metodologi sebagai cara untuk menjawab rumusan.

## Identifikasi Masalah

1. Informasi mengenai bahan, tata cara penyiapan berkas desain, dan estimasi biaya di Asia Visual belum terdokumentasi secara tertulis, belum terpusat, dan belum tersedia otomatis selama 24 jam.
2. Admin harus menjawab pertanyaan pelanggan yang berulang secara manual melalui WhatsApp, sehingga beban kerja meningkat seiring bertambahnya pemesanan daring.
3. Pelanggan bertanya dengan bahasa informal, singkatan, salah ketik, dan campuran bahasa daerah, sehingga chatbot berbasis kata kunci sulit menjawabnya.
4. LLM tanpa sumber informasi usaha berisiko menghasilkan jawaban keliru (halusinasi), sehingga RAG perlu diterapkan dan kinerjanya dibuktikan pada layanan informasi UMKM *digital printing*.

## Rumusan Masalah

Seberapa baik kinerja chatbot WhatsApp berbasis *Retrieval-Augmented Generation* (RAG) dengan basis pengetahuan yang disusun dari kondisi Asia Visual sebagai layanan informasi *digital printing*, ditinjau dari kinerja *retrieval* (*Hit Rate*, *Precision*, dan *Recall*), kualitas jawaban (*Human Evaluation*), dan kebergunaan sistem (SUS)?

## Tujuan Penelitian

Menyusun basis pengetahuan dan mengimplementasikan chatbot WhatsApp berbasis RAG sebagai layanan informasi *digital printing* pada Asia Visual, kemudian mengukur kinerjanya berdasarkan *Hit Rate*, *Precision*, *Recall*, *Human Evaluation*, dan SUS.

## Batasan Masalah

1. Chatbot hanya berfungsi sebagai layanan informasi mengenai jenis bahan dan produk, panduan penyiapan berkas desain, dan estimasi biaya cetak.
2. Chatbot tidak memproses pembayaran, tidak menerima atau mengelola berkas desain, dan tidak menangani transaksi pemesanan.
3. Chatbot dijalankan melalui WhatsApp dengan satu model LLM berbayar berbiaya rendah, yaitu **[nama model]**.
4. Basis pengetahuan disusun oleh peneliti berdasarkan kondisi aktual Asia Visual melalui wawancara dan observasi data chat 2025, serta divalidasi oleh pihak Asia Visual.

## Pemetaan Rantai

| Identifikasi | Rumusan | Tujuan | Kesimpulan |
|---|---|---|---|
| 1 sampai 4 | Seberapa baik kinerja chatbot... | Menyusun knowledge base, mengimplementasikan chatbot, dan mengukur kinerjanya | Chatbot berhasil dibangun dengan **[arsitektur ringkas]**. *Hit Rate* **[X]**, *Precision* **[X]**, *Recall* **[X]**, *Human Evaluation* **[X]**, SUS **[X]**, sehingga kinerja dinilai **[baik/belum baik]** terhadap ambang batas **[...]** |

## Yang perlu dijaga

- Kata "baik" harus punya ambang batas di metodologi (misalnya SUS ≥ 68, plus batas *Hit Rate* dan skor *Human Evaluation* beserta alasannya).
- Identifikasi 1 sampai 3 dijawab lewat tahap pembangunan sistem (di tujuan), sedangkan identifikasi 4 dijawab lewat hasil pengujian. Pastikan bab hasil menjelaskan kaitan ini.
- Bagian penyusunan knowledge base, *chunking*, embedding, dan integrasi WhatsApp tetap ditulis di Bab 3 meski tidak menjadi rumusan sendiri.

Mau saya lanjutkan dengan manfaat penelitian atau draf Bab 3 (tahapan metodologi)?