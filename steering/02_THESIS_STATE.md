# 02_THESIS_STATE.md — Kondisi & Status Skripsi Real-Time

> 📌 **UNTUK APA FILE INI:** Catatan status real-time progres penulisan naskah Bab 1 s.d. 6 dan ringkasan 4 tabel hasil pengujian terkunci.

Dokumen ini memantau perkembangan skripsi secara real-time, mencakup progres penulisan bab, status eksperimen/evaluasi, dan daftar tugas prioritas.

---

## 1. Informasi Penelitian & Skripsi
- **Judul Skripsi (LOCKED):** Implementasi Chatbot Informasi Usaha Percetakan Menggunakan Retrieval-Augmented Generation (Studi Kasus: CV. Asia Visual Grafika)
- **Nama Mahasiswa:** Nadhif Ali Ikhsani (NIM: 11210910000062)
- **Program Studi:** Teknik Informatika, Fakultas Sains dan Teknologi, UIN Syarif Hidayatullah Jakarta
- **Dosen Pembimbing 1:** Bapak Muhamad Azhari, M.Kom.
- **Dosen Pembimbing 2:** Ibu Fitri Mintarsih, M.Kom.
- **Dosen Penguji 1:** Ibu Viva Arifin, M.Kom.
- **Dosen Penguji 2:** Ibu Nurul Faizah (Bu Faiz), M.Kom.
- **Target Ujian Sidang:** Akhir Oktober / Awal November 2026 (Deadline Mutlak Pendaftaran: 11 November 2026)
- **LAKSAMANA WAKTU MUTLAK SKRIPSI:**
  - 🛑 **10 OKTOBER 2026:** DEADLINE MUTLAK NASKAH UTUH (BAB 1 - 5) SELESAI 100% (Wajib mulai proses bimbingan & ACC 4 Dosen: Pak Azhari, Bu Fitri, Bu Viva, Bu Faiz).
  - 🛑 **04 NOVEMBER 2026:** BATAS AKHIR PENDAFTARAN SIDANG KE TU FST UIN (Semua tanda tangan ACC 4 Dosen harus sudah lengkap & jadwal diselaraskan).
  - 🛑 **11 NOVEMBER 2026:** BATAS AKHIR MUTLAK SIDANG SELESAI & NILAI SUDAH HARUS INPUT SIAKAD.
- **STATUS TEKNIS & KODE:** 🔒 **PROJECT COMPLETE & CODE SEALED 100% (DEC-016)** — Pengembangan teknis dan kodingan sistem Chatbot RAG resmi SELESAI 100% dan DIKUNCI MATI. Seluruh bug teratasi, Knowledge Base 6 dokumen lengkap (`01_` s.d. `06_`), histori multi-turn stabil via prompt, dan portal admin siap pakai. Dilarang keras menambah/mengedit kode baru.

---

## 2. Progres Penulisan Bab (Struktur Resmi 6 Bab FST UIN Jakarta)

> ⚠️ **Update 6 Oktober 2026:** Audit menyeluruh dokumen Word `REFISI SKRIPSI.docx` sudah dilakukan. Status di bawah mencerminkan kondisi dokumen Word nyata, bukan estimasi.

- [ ] **BAB I - Pendahuluan:**
  - Status di Word: 🟡 **SEBAGIAN** — Latar Belakang ada tapi perlu tambahan data. Identifikasi Masalah, Rumusan, Batasan, Tujuan, Manfaat → **semua kosong/placeholder**.
  - Update 1 Okt:
    - Latar Belakang: 🟢 Draf lengkap 8 paragraf selesai (siap copy ke Word)
    - Batasan Masalah Alat: 🟢 Draf final 9 poin selesai (siap copy ke Word)
    - Batasan Masalah Metode: 🟢 Draf 3 poin selesai (siap copy ke Word)
    - Batasan Masalah Proses: 🔴 Belum dibuat
    - Identifikasi Masalah: 🔴 Belum dibuat
    - Rumusan Masalah: 🔴 Belum dibuat
    - Tujuan & Manfaat: 🔴 Belum dibuat

- [ ] **BAB II - Tinjauan Pustaka & Landasan Teori:**
  - Status di Word: 🟡 **SEBAGIAN** — Chatbot, NLP, LLM, Transformer, Prompt Eng, RAG, Embedding, Prototyping, Python, OpenRouter, LangChain sudah ada.
  - Yang masih kosong: FastAPI, Gemini 2.5 Flash, HuggingFace Embedding, ChromaDB, CV. Asia Visual Grafika.
  - Tabel Literatur Sejenis: 7/15 judul terisi, semua kolom isi kosong. Tabel Pembeda juga kosong semua.
  - Catatan dosen: Pindahkan tabel literatur ke paling akhir, cari penelitian sejenis tema layanan informasi/percetakan, miringkan istilah asing.

- [ ] **BAB III - Metode Penelitian:**
  - Status di Word: 🟡 **SEBAGIAN** — Alur penelitian (gambar placeholder), wawancara, observasi, studi dokumen, studi literatur sudah ada.
  - Update 2 Okt: 
    - Latar Belakang: 🟢 Draf lengkap 8 paragraf selesai (siap copy ke Word)
    - Batasan Masalah Alat: 🟢 Draf final 9 poin selesai (siap copy ke Word)
    - Batasan Masalah Metode: 🟢 Draf 3 poin selesai (siap copy ke Word)
    - Identifikasi Masalah: 🟢 Final 2 poin siap copy ke Word
    - Rumusan Masalah: 🟢 Final 2 poin siap copy ke Word
    - Batasan Masalah Proses: 🔴 Belum dibuat
    - Tujuan Penelitian: 🔴 Belum dibuat
    - Manfaat Penelitian: 🔴 Belum dibuat
  - Yang masih kosong: Quick Planning, Quick Modelling, Konstruksi, Pengujian, semua diagram.

- [ ] **BAB IV - Analisis, Perancangan, Implementasi & Pengujian:**
  - Status di Word: 🟢 **BAHAN SELESAI 100% DI PEMAHAMAN_SISTEM.MD** — Tinggal dipindahkan ke Word.
  - Komponen: Tahap Komunikasi, Ruang Lingkup, Tabel KB (6 file), Alur RAG, Alur Chatbot, Use Case, Activity Diagram, Penyusunan KB, Implementasi RAG, Pembuatan Antarmuka Admin, Tahap Pengujian.

- [ ] **BAB V - Hasil dan Pembahasan:**
  - Status di Word: 🟡 **DATA LENGKAP DI PEMAHAMAN_SISTEM.MD**
  - Tabel Black Box (10 skenario): 🟢 Ada, semua "Sesuai"
  - Tabel Akurasi Retrieval: 🟢 Hit Rate@3 = 100.0%, Precision@3 = 56.67% dari 10 pertanyaan acuan
  - Tabel SUS: 🟢 20 Responden (pelanggan & CS toko)
  - Tabel Human Evaluation: 🟢 Penilaian kualitatif kesopanan, kelayakan, & ketepatan harga
  - Pembahasan: 🔴 Belum dimasukkan ke Word

- [ ] **BAB VI - Kesimpulan dan Saran:**
  - Status di Word: 🔴 **KOSONG TOTAL**

---

## 3. Status Eksperimen & Evaluasi Sistem
- **Dataset Pengetahuan RAG:** 6 berkas `.txt` lengkap (`01_` s.d. `06_`), mencakup 100% harga produk, SOP, berkas siap cetak, FAQ menu, estimasi pcs stiker A3+, dan spesifikasi bahan.
- **Dataset Bukti Empiris:** 500 sesi percakapan dianalisis dari total 4.052 sesi (`dataset/raw/(01)_data_chat_customer.csv`)
- **Arsitektur Sistem:** Pure Naive RAG WhatsApp Chatbot (ChromaDB + Gemini 2.5 Flash + History-in-Prompt + WhatsApp Webhook API)
- **Status Teknis:** 🔒 **SELESAI 100% & DIKUNCI (DEC-016)** — Sistem siap diuji. Tidak ada penambahan fitur apapun.

---

## 4. STATUS FASE SAAT INI: PENGUJIAN + PENULISAN NASKAH (10 HARI)

> ⏰ **Mulai: 29 September 2026 — Target: 9 Oktober 2026 (Naskah Utuh Siap ACC)**

### Pengujian yang WAJIB Diselesaikan (PAS 4 TABEL BAB V):

| No | Jenis Pengujian | Metode | Subjek | Status |
|----|----------------|--------|--------|--------|
| 1 | **Black Box Fungsionalitas** | Ceklis 10 Skenario PASS/FAIL (RAG WA + Admin) | Dif sendiri | 🟢 Ada di Word (10 skenario "Sesuai") |
| 2 | **Akurasi Retrieval** | Hit Rate@3=100%, Precision@3=56.67% dari `testing/tabel_akurasi_retrieval.csv` | 10 Pertanyaan Uji Acuan | 🟢 Data Selesai |
| 3 | **SUS / UAT (Usability)** | Kuesioner SUS standar 10 pertanyaan (post-implementation) | 20 Responden (Pelanggan & CS) | 🟢 20 Responden Terkumpul |
| 4 | **Human Evaluation** | Penilaian Relevansi/Kelengkapan/Kejelasan | Penilai Manusia (CS/Admin Toko) | 🟢 Data Siap |

> 📌 **Catatan Alur Pra-Penelitian Bab I & III (LOCKED):** Wawancara 1 (Mas Aji SPV) → Observasi Chat WA 2025 (4.052 chat, sampel 500) → Wawancara 2 (Rizky Admin/Setter). Tidak ada kuesioner awal untuk Bab I.

### Penulisan Bab yang WAJIB Diselesaikan:

| Bab | Status di Word | Prioritas |
|-----|--------|-----------|
| Bab I - Pendahuluan | 🟡 LB ada, sisanya kosong | Isi Identifikasi, Rumusan, Batasan, Tujuan, Manfaat |
| Bab II - Tinjauan Pustaka | 🟡 Sebagian — 5 sub-bab kosong, tabel literatur kosong | Isi FastAPI, ChromaDB, Gemini, HuggingFace, CV Asia, Tabel Literatur |
| Bab III - Metode Penelitian | 🟡 Pengumpulan data ada, Prototyping 5 tahap kosong | Isi 5 tahap Prototyping + buat diagram |
| Bab IV - Implementasi | 🔴 Mayoritas kosong | Prioritas tinggi — isi semua sub-bab konstruksi |
| Bab V - Pengujian & Pembahasan | 🟡 Sebagian — perbaiki rata-rata, tambah DeepSeek, isi SUS & HE | **PRIORITAS setelah data SUS & HE terkumpul** |
| Bab VI - Kesimpulan & Saran | 🔴 Kosong total | Tulis setelah Bab V & Rumusan Masalah selesai |

### Prioritas Aksi Hari Ini (1 Oktober 2026 — Hari ke-3):
1. 🎯 **Buat instrumen SUS** (10 pertanyaan standar) → sebarkan ke 10–15 orang hari ini
2. 🎯 **Buat instrumen Human Evaluation** → kirim ke Mba Intan, Rizky, Shinta
3. 🎯 **Isi Rumusan Masalah + Identifikasi Masalah Bab I** → kunci semua bab lain

