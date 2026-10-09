# STEERING & WORKSPACE MEMORY — Chatbot RAG CV. Asia Visual Grafika (Skripsi)

> [!IMPORTANT]
> **PANDUAN DAN MEMORI WAJIB AGENT**:
> Dokumen ini adalah acuan permanen (*steering rules*) yang mengikat seluruh sesi asistensi untuk penulisan naskah skripsi ini. Agent WAJIB mematuhi seluruh ketetapan di bawah ini tanpa kecuali.

---

## 1. Identitas Proyek & Arsitektur Sistem Terkunci
* **Judul/Domain**: Chatbot Informasi Percetakan Digital berbasis *Retrieval-Augmented Generation* (RAG).
* **Objek Penelitian**: CV. Asia Visual Grafika (Percetakan Digital Tangerang Selatan: Cabang Ciputat Timur & Pamulang Barat).
* **Kanal Integrasi**: WhatsApp (via Fonnte API Gateway Webhook) dan Portal Web Admin lokal (`/admin`).
* **Komponen AI Terkunci**:
  * **LLM**: Google Gemini 2.5 Flash via OpenRouter (`google/gemini-2.5-flash`), *temperature* = 0.0, *max_tokens* = 1024.
  * **Embedding**: HuggingFace Lokal `intfloat/multilingual-e5-small` (384 dimensi) dengan *wrapper* awalan *passage:* dan *query:*.
  * **Vectorstore**: ChromaDB lokal (`./chroma_db`) dengan metrik jarak *Cosine Distance* (`hnsw:space: cosine`).
* **Basis Data Pengetahuan**: 6 berkas teks di `dataset/knowledge_base/` (`01_sop` s.d. `06_estimasi`).
* **Riwayat Percakapan**: Memori aktif *History-in-Prompt* (maksimal 2 *turn*) dan arsip permanen di `dataset/admin_chat_history.json`.
* **Prinsip File**: Fokus pada berkas yang aktif di proyek saat ini (dilarang me-*recover* berkas lama yang sudah dihapus).

---

## 2. Format Baku Naskah Akademik (Ketentuan Skripsi)
Sesuai panduan format resmi institusi:
1. **Struktur Bab Lengkap (Bab I s.d. Bab VI)**:
   * **Bab I**: Pendahuluan
   * **Bab II**: Tinjauan Pustaka / Landasan Teori
   * **Bab III**: Metode Penelitian
   * **Bab IV**: Analisis, Desain, Implementasi dan Pengujian
   * **Bab V**: Hasil dan Pembahasan
   * **Bab VI**: Penutup (Kesimpulan dan Saran)
2. **Ketebalan Halaman Wajib**: Minimal 80 halaman murni dari Bab I hingga Bab VI (tidak termasuk bagian Romawi, Daftar Pustaka, Lampiran).
3. **Pengaturan Kertas & Margin**: Kertas HVS A4 80 gram, Margin: Atas 4 cm, Kiri 4 cm, Bawah 3 cm, Kanan 3 cm.
4. **Font & Spasi**: Times New Roman 12pt dengan spasi tunggal (1.0) untuk naskah utama.
5. **Penomoran Hirarkis Baku (Anti-Bullet Point)**: 
   * **DILARANG KERAS** menggunakan simbol *bullet point* (`•`, `-`, `✓`) di dalam paragraf naskah.
   * Wajib menggunakan hirarki resmi:
     `BAB IV` $\rightarrow$ `A.` $\rightarrow$ `1.` $\rightarrow$ `a.` $\rightarrow$ `1)` $\rightarrow$ `a)` $\rightarrow$ `(1)` $\rightarrow$ `(a)`.
6. **Format Tabel & Gambar**:
   * **Tabel**: Format Tabel Ilmiah Terbuka (hanya garis horizontal di *header* dan penutup, tanpa garis vertikal). Judul tabel diletakkan di **ATAS** tabel.
   * **Gambar**: Judul gambar diletakkan di **ATAS** gambar. Setiap gambar wajib diikuti narasi penjelasan di bawahnya.
7. **Cetak Miring (*Italic*)**: Seluruh istilah asing atau teknis (*retrieval*, *chunking*, *embedding*, *vector database*, *latency*, *webhook*, *framework*, *pipeline*, *turn*, *wrapper*, dll.) **WAJIB** dicetak miring.

---

## 3. Aturan Khusus Penulisan Dokumentasi Bab IV (Teknik Sandwich)
1. **Teknik Sandwich (Wajib)**:
   * Pola penulisan: **[Narasi Pembuka] $\rightarrow$ [Tengah: Cuplikan Kode / Gambar] $\rightarrow$ [Narasi Penjelas di Bawah]**.
   * Tidak boleh ada kode/gambar yang menempel tanpa narasi pengantar di atasnya atau narasi bedah detail di bawahnya.
2. **Kepadatan Narasi Berimbang (Pas)**:
   * **Ukuran Narasi**: Dibuat pas dan berimbang (1–2 paragraf sedang per poin, tidak terlalu panjang bertele-tele dan tidak terlalu pendek 1 baris).
3. **Gaya Bahasa**:
   * Menggunakan gaya bahasa mahasiswa akademik dengan kombinasi kalimat aktif dan pasif yang mengalir (misal: "Penulis mengonfigurasi...", "Sistem memproses...", "Fungsi ini dijalankan untuk...").
   * Ditulis layaknya sebuah **tutorial pembuatan secara runtut** dari langkah awal hingga akhir (*step-by-step* yang runut).
4. **Larangan Istilah Teknis Matematika**:
   * **DILARANG** mencantumkan rumus, perhitungan matematis rumit, atau simbol/istilah teknis matematika (*ceiling, floor, formula sigma*, dll.). Jelaskan logika alur secara deskriptif, logis, dan alamiah.
5. **Batasan Cuplikan Kode (*Source Code*)**:
   * Cuplikan kode **maksimal tidak boleh melebihi 1 halaman penuh**.
   * Wajib hanya mengambil cuplikan fungsi/baris kode yang sedang dibahas secara spesifik (bukan *dump* satu berkas utuh).
   * Tandai secara eksplisit sebagai *Source Code* atau *Listing Program* (bukan tabel/gambar biasa).
6. **Pencantuman Placeholder Gambar**:
   * Jangan terlalu banyak tabel dan gambar.
   * Jika memerlukan gambar, wajib mencantumkan instruksi eksplisit nama gambar yang harus ditempel di Word dengan format:
     `[Narasi Pengantar]` $\rightarrow$ **Gambar X.X: [Nama Gambar yang Harus Dicari/Ditempel]** $\rightarrow$ `[Narasi Penjelas]`.

---

## 4. SISTEMATIKA RESMI TERKUNCI (FIX DARI PENGGUNA)

### BAB IV: ANALISIS, DESAIN, IMPLEMENTASI DAN PENGUJIAN
*(Target: ~50 Halaman)*

* **A. Tahap Komunikasi**
  *(Bagian ini ditulis narasi saja)*
* **B. Tahap Perencanaan Cepat**
  * 1. Ruang Lingkup dan Batasan Sistem
  * 2. Analisis Kebutuhan Fungsional
  * 3. Analisis Kebutuhan Perangkat Keras dan Lunak
* **C. Tahap Pemodelan Cepat**
  * 1. Desain *Knowledge Base*
  * 2. Desain Alur RAG
  * 3. Desain Alur *Chatbot*
  * 4. *Use Case Diagram*
  * 5. *Activity Diagram*
* **D. Tahap Konstruksi**
  * 1. Lingkungan Implementasi
  * 2. Penyusunan *Knowledge Base*
  * 3. Implementasi Alur RAG
  * 4. Pembuatan *Chatbot* WhatsApp
  * 5. Pembuatan Antarmuka
* **E. Tahap Pengujian**
  *(Bagian ini ditulis narasi saja)*

---

### BAB V: HASIL DAN PEMBAHASAN
*(Membahas data empiris, pengujian detail, dan pembahasan mendalam)*

* **A. Hasil Pengujian**
  * 1. Hasil Pengujian Fungsional
  * 2. Hasil Pengujian *Retrieval*
  * 3. Hasil *System Usability Scale* (SUS)
  * 4. Hasil *Human Evaluation*
* **B. Pembahasan**

---

### BAB VI: PENUTUP
* **A. Kesimpulan**
* **B. Saran**
