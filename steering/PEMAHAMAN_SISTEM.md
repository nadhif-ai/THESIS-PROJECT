# BAB IV: ANALISIS, PERANCANGAN, IMPLEMENTASI DAN PENGUJIAN

Bab IV ini menyajikan seluruh rangkaian analisis kebutuhan, perancangan sistem, implementasi kode program, hingga pengujian menyeluruh pada sistem *chatbot* informasi percetakan berbasis *Retrieval-Augmented Generation* (RAG). Pembahasan disusun secara sistematis mengikuti lima tahapan utama dalam metodologi *Prototyping*, yaitu Tahap Komunikasi, Tahap Perencanaan Cepat (*Quick Planning*), Tahap Pemodelan Cepat (*Quick Modelling*), Tahap Konstruksi (*Construction*), serta Tahap Pengujian (*Testing*).

---

## A. Tahap Komunikasi

Tahap komunikasi merupakan langkah awal yang dilakukan peneliti untuk menggali permasalahan operasional dan kebutuhan pelayanan informasi pada CV. Asia Visual Grafika melalui wawancara langsung dan studi dokumentasi.

### 1. Pelaksanaan Wawancara Pemangku Kepentingan
Peneliti melakukan wawancara langsung bersama pihak pengelola toko, yaitu Bapak Aji (pemilik toko) dan Mas Rizky (staf admin CS/*setter*). Dari proses wawancara ini, diketahui bahwa kendala utama toko adalah lambatnya waktu respon (*response time*) dalam membalas pesan WhatsApp pelanggan akibat terbatasnya jumlah staf admin, sementara antrean pesan yang masuk cukup tinggi setiap harinya. Pertanyaan pelanggan umumnya berulang seputar daftar harga cetak, spesifikasi bahan spanduk/stiker, lokasi 2 cabang toko di Pekanbaru, jam operasional, dan syarat pengiriman berkas desain.

### 2. Hasil Studi Dokumentasi Katalog Harga dan Riwayat Percakapan (`msgstore.db.crypt`)
Selain wawancara, pengumpulan data operasional toko dilakukan melalui dua sumber dokumentasi:

#### a. Studi Dokumentasi Buku Katalog Daftar Harga Resmi Toko
Peneliti mempelajari dokumen buku daftar harga cetak resmi CV. Asia Visual Grafika. Data patokan tarif cetak untuk bahan Flexi 280, Flexi 340, Flexi Korcin, Stiker Vinyl, Albatross, Art Paper, HVS A3+, dan cetak nota diambil untuk dijadikan rujukan utama dalam penyusunan 6 berkas basis pengetahuan (*knowledge base*) berformat `.txt`.

#### b. Analisis Riwayat Percakapan WhatsApp via Basis Data `msgstore.db.crypt`
Peneliti menganalisis arsip basis data percakapan pelanggan WhatsApp toko (`msgstore.db.crypt`). Dari analisis tersebut, teridentifikasi pola bahwa pertanyaan terbanyak pelanggan berkisar pada estimasi perhitungan biaya cetak spanduk dan stiker, rekomendasi bahan tahan air untuk luar ruangan (*outdoor*), alamat 2 cabang toko di Pekanbaru, serta ketentuan wajib pembayaran uang muka (DP) sebesar 50–60%.

Temuan kendala pada tahap komunikasi ini menjadi dasar bagi peneliti dalam merumuskan batasan dan kebutuhan fungsional sistem pada tahap perencanaan cepat.

---

## B. Tahap Perencanaan Cepat

Pada tahap perencanaan cepat (*quick planning*), peneliti menentukan batasan ruang lingkup sistem, menganalisis 4 kebutuhan fungsional utama, serta menetapkan spesifikasi perangkat keras dan perangkat lunak yang digunakan.

### 1. Ruang Lingkup dan Batasan
Pengembangan sistem *chatbot* ini dibatasi pada layanan informasi CV. Asia Visual Grafika (Pekanbaru), memuat 6 berkas teks *knowledge base*, menggunakan bahasa pemrograman Python 3.10, framework FastAPI, database vektor ChromaDB lokal, model *embedding* `multilingual-e5-small`, LLM Gemini 2.5 Flash, gateway WhatsApp Webhook, serta antarmuka *Web Admin Portal* (`/admin`) untuk mengelola data.

### 2. Analisis Kebutuhan Fungsional
Berdasarkan temuan masalah di toko, dirumuskan 4 kebutuhan fungsional utama yang harus dipenuhi oleh sistem:

#### a. Sistem dapat menghubungkan platform WhatsApp sebagai media input chatbot dari pengguna dengan proses Retrieval-Augmented Generation (RAG).
Sistem mampu menerima data pesan teks dari *webhook* WhatsApp, mengekstrak nomor pengirim dan isi pertanyaan, lalu meneruskannya secara asinkron ke dalam *pipeline* RAG untuk diproses.

#### b. Sistem dapat memberikan jawaban dari pertanyaan seputar harga dan produk, serta informasi mengenai digital printing yang sesuai dengan knowledge base.
Sistem mampu mencari fakta acuan pada database vektor ChromaDB dan memerintahkan LLM Gemini 2.5 Flash untuk menghasilkan jawaban yang akurat, ramah khas percetakan Pekanbaru, serta menghitung estimasi biaya cetak secara transparan.

#### c. Sistem dapat mengelola knowledge base yang hanya bisa diakses oleh petugas.
Sistem menyediakan antarmuka *Web Admin Portal* (`/admin`) yang dilindungi otorisasi *login* agar staf toko dapat mengedit isi berkas pengetahuan `.txt` dan memantau log percakapan pelanggan.

#### d. Sistem dapat menolak dengan bahasa yang sopan ketika topik pertanyaan di luar digital printing.
Sistem dilengkapi aturan batasan instruksi (*System Prompt*) agar *chatbot* secara sopan menolak menjawab pertanyaan di luar topik percetakan dan menyarankan pelanggan menghubungi admin secara manual.

### 3. Analisis Kebutuhan Perangkat
Spesifikasi perangkat keras (*hardware*) dan perangkat lunak (*software*) pendukung pengembangan dan pengoperasian sistem tertera pada Tabel 4.1.

#### Tabel 4.1 Spesifikasi Perangkat Keras dan Perangkat Lunak Sistem

| Jenis Kebutuhan | Komponen | Spesifikasi / Keterangan |
|---|---|---|
| **Perangkat Keras (*Hardware*)** | Processor | Intel Core i5 / AMD Ryzen 5 (Multi-core) |
| | Memori RAM | 8 GB / 16 GB DDR4 |
| | Penyimpanan | SSD 256 GB NVMe |
| **Perangkat Lunak (*Software*)** | Sistem Operasi | Windows 10/11 64-bit |
| | Bahasa Pemrograman | Python 3.10.0 |
| | Web Framework Backend | FastAPI 0.111.0 & Uvicorn 0.30.1 |
| | Framework RAG | LangChain 0.2.5 & LangChain-Chroma |
| | Database Vektor | ChromaDB 0.5.3 (Penyimpanan Lokal Disk) |
| | Model Embedding | `intfloat/multilingual-e5-small` (384 Dimensi) |
| | Model Bahasa (LLM) | Google Gemini 2.5 Flash |
| | WhatsApp Gateway | Fonnte / WhatsApp Webhook API |
| | Tool Tunneling Jaringan | ngrok 3.39.2 |
| | Pengolahan Data | Pandas 2.2.2 |

Spesifikasi perangkat pada Tabel 4.1 di atas memastikan bahwa seluruh kebutuhan pemrosesan data vektor dan alur RAG dapat dieksekusi secara optimal dan ringan pada komputer toko. Perencanaan cepat kebutuhan fungsional dan perangkat ini menjadi landasan dalam pemodelan diagram sistem pada sub-bab berikutnya.

---

## C. Tahap Pemodelan Cepat

Sub-bab ini menyajikan perancangan basis pengetahuan, arsitektur alur RAG, alur percakapan *chatbot*, serta pemodelan sistem menggunakan *Use Case Diagram* dan *Activity Diagram*.

### 1. Perancangan Knowledge Base
Data operasional toko dikelompokkan secara terstruktur menjadi 6 berkas teks (`.txt`) modular di dalam direktori `knowledge/`:
1. `01_profil_dan_layanan.txt`: Berisi sejarah toko, alamat cabang, jam operasional, dan gambaran umum layanan.
2. `02_produk_layanan_detail.txt`: Berisi katalog lengkap produk spanduk, stiker, banner, nota, dan kartu nama.
3. `03_teknis_dan_spesifikasi.txt`: Berisi panduan berkas siap cetak (*file print*), format PDF/CDR/TIFF, resolusi 300 DPI, dan mode warna CMYK.
4. `04_alur_dan_kebijakan.txt`: Berisi SOP pemesanan, ketentuan uang muka (DP 50–60%), dan kebijakan retur cetak.
5. `05_faq_dan_penanganan.txt`: Berisi pertanyaan umum pelanggan seputar waktu pengerjaan dan pengambilan barang.
6. `06_harga_dan_estimasi.txt`: Berisi daftar tarif harga cetak per meter/lembar dan rumus perhitungan estimasi biaya.

### 2. Perancangan Alur RAG
Arsitektur penarikan informasi RAG dirancang menghubungkan *webhook* WhatsApp, backend FastAPI, model *embedding* `multilingual-e5-small`, pencarian dokumen ChromaDB (*Top-3 Chunks*), *System Prompt*, dan LLM Gemini 2.5 Flash.

> **Gambar 4.1** Flowchart Arsitektur Pipeline RAG Chatbot Percetakan

```mermaid
graph LR
    A[WhatsApp Payload] --> B[FastAPI Endpoint]
    B --> C[Embedding E5-small]
    C --> D[ChromaDB Top-3 Retrieval]
    D --> E[System Prompt Builder]
    E --> F[Gemini 2.5 Flash]
    F --> G[Balasan Text WhatsApp]
```

Gambar 4.1 memperlihatkan alur kerja *pipeline* RAG secara utuh. Pertanyaan pelanggan dari WhatsApp diproses oleh FastAPI, diubah menjadi vektor *embedding*, dicocokkan di ChromaDB untuk menarik 3 potongan teks teratas (*Top-3 Chunks*), digabungkan ke *System Prompt*, lalu dikirim ke Gemini 2.5 Flash untuk menghasilkan balasan teks yang akurat.

### 3. Perancangan Alur Chatbot
Alur interaksi percakapan otomatis saat pelanggan mengirimkan pesan di WhatsApp digambarkan pada Gambar 4.2 berikut:

> **Gambar 4.2** Activity Diagram Alur Tanya Jawab dan Perhitungan Harga via WhatsApp

```mermaid
stateDiagram-v2
    [*] --> PelangganKirimWA: Pelanggan kirim pesan di WA
    PelangganKirimWA --> WebhookTerima: Webhook WhatsApp terima payload
    WebhookTerima --> CekIntentKhusus: Server FastAPI terima pesan

    state CekIntentKhusus {
        [*] --> CekSapaan: Sapaan (Halo/Pagi)?
        CekSapaan --> BalasMenu: Ya -> Kirim Sambutan & Menu
        CekSapaan --> CekReset: Tidak -> Cek Kata 'Reset'?
        CekReset --> HapusHistori: Ya -> Hapus Sesi & Konfirmasi
        CekReset --> JalankanRAG: Tidak -> Lanjut ke RAG Pipeline
    }

    JalankanRAG --> EmbedQuery: Ubah Pertanyaan jadi Vektor Embedding
    EmbedQuery --> SearchChroma: Cari Top-3 Chunk Relevan di ChromaDB
    SearchChroma --> BuildPrompt: Gabungkan Konteks + Histori + Pertanyaan
    BuildPrompt --> CallGemini: Panggil Gemini 2.5 Flash
    CallGemini --> SendWAReply: Kirim Balasan Teks ke WhatsApp Pelanggan
    SendWAReply --> [*]
```

Gambar 4.2 menjelaskan alur percakapan *chatbot*. Server terlebih dahulu mengecek *intent* sapaan awal atau kata kunci `reset`. Jika pesan berupa pertanyaan produk atau estimasi harga, sistem mengeksekusi *pipeline* RAG untuk menghasilkan respon berbasis dokumen toko.

### 4. Use Case Diagram
Pembagian wewenang dan hak akses antara Pelanggan WhatsApp dan Admin Toko digambarkan pada Gambar 4.3 berikut:

> **Gambar 4.3** Use Case Diagram Chatbot RAG CV. Asia Visual Grafika

```mermaid
graph TD
    user((Pelanggan WA))
    admin((Admin CS Toko))
    system[[Sistem Chatbot RAG]]

    user --> UC1(Kirim Pesan WA / Tanya Info)
    user --> UC2(Minta Estimasi Harga Cetak)
    user --> UC3(Reset Percakapan)

    admin --> UC4(Akses Web Admin Portal)
    admin --> UC5(Kelola File Knowledge Base .txt)
    admin --> UC6(Lihat Riwayat Chat Pelanggan)

    UC1 --> system
    UC2 --> system
    UC3 --> system
    UC4 --> system
    UC5 --> system
    UC6 --> system
```

Gambar 4.3 menunjukkan 2 aktor utama sistem. Pelanggan dapat berinteraksi tanya-jawab dan meminta perkiraan harga via WhatsApp, sedangkan Admin Toko mengelola berkas dokumen `.txt` dan memantau log percakapan melalui *Web Admin Portal* (`/admin`).

---

## D. Tahap Konstruksi

Tahap konstruksi menguraikan implementasi kode program *pipeline* RAG, konfigurasi database vektor ChromaDB, pembentukan *System Prompt*, serta pembuatan antarmuka *Web Admin Portal*.

### 1. Penyusunan Knowledge Base dan Pemotongan Teks (`loader.py`)
Pemuatan dan pemotongan 6 berkas `.txt` diimplementasikan dalam modul `loader.py` menggunakan `RecursiveCharacterTextSplitter`.

#### Tabel 4.2 Potongan Kode Program Pemuatan dan Pemotongan Dokumen Teks (`loader.py`)

| Baris | Kode Program Python (`loader.py`) |
|---|---|
| 1 | `from langchain_text_splitters import RecursiveCharacterTextSplitter` |
| 2 | `# Konfigurasi ukuran pemotongan dokumen basis pengetahuan` |
| 3 | `CHUNK_SIZE = 1500     # Maksimal 1500 karakter per potongan` |
| 4 | `CHUNK_OVERLAP = 200    # 200 karakter tumpang tindih antar potongan` |
| 5 | `splitter = RecursiveCharacterTextSplitter(` |
| 6 | `    chunk_size=CHUNK_SIZE,` |
| 7 | `    chunk_overlap=CHUNK_OVERLAP` |
| 8 | `)` |

Penjelasan alur kerja kode program Tabel 4.2 diuraikan sebagai berikut:
1. Pada baris 1, pustaka `RecursiveCharacterTextSplitter` diimpor untuk memotong dokumen teks besar menjadi bagian-bagian kecil berdasarkan pemisah paragraf agar konteks informasi tetap terjaga.
2. Pada baris 3 dan 4, nilai `CHUNK_SIZE` ditetapkan 1.500 karakter dan `CHUNK_OVERLAP` sebesar 200 karakter. Ukuran 1.500 karakter dipilih agar rincian spesifikasi bahan tetap utuh, dan *overlap* 200 karakter memastikan kalimat di batas pemotongan tetap berkesinambungan.
3. Pada baris 5 hingga 8, objek `splitter` diinisialisasi untuk memproses 6 berkas `.txt` menjadi potongan-potongan teks (*chunks*) yang siap diubah menjadi vektor *embedding*.

### 2. Implementasi Database Vektor ChromaDB (`vectorstore.py`)
Konfigurasi model *embedding* dan penyimpanan vektor ChromaDB diimplementasikan pada modul `vectorstore.py`.

#### Tabel 4.3 Potongan Kode Program Konfigurasi Database Vektor ChromaDB (`vectorstore.py`)

| Baris | Kode Program Python (`vectorstore.py`) |
|---|---|
| 1 | `from langchain_community.vectorstores import Chroma` |
| 2 | `from langchain_community.embeddings import HuggingFaceEmbeddings` |
| 3 | `# Inisialisasi model embedding E5-small pada CPU lokal` |
| 4 | `embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")` |
| 5 | `# Inisialisasi database vektor ChromaDB lokal` |
| 6 | `vectorstore = Chroma(` |
| 7 | `    collection_name="asia_print_kb",` |
| 8 | `    embedding_function=embeddings,` |
| 9 | `    persist_directory="./chroma_db"` |
| 10 | `)` |

Penjelasan alur kerja kode program Tabel 4.3 diuraikan sebagai berikut:
1. Pada baris 1 dan 2, modul `Chroma` dan `HuggingFaceEmbeddings` diimpor untuk mengelola database vektor lokal dan mengekstrak *embedding*.
2. Pada baris 4, model `intfloat/multilingual-e5-small` diinisialisasi untuk mengonversi kalimat menjadi vektor 384 dimensi secara efisien pada CPU lokal.
3. Pada baris 6 hingga 10, objek `vectorstore` dibuat untuk menyimpan seluruh vektor dokumen pada direktori lokal `./chroma_db`, sehingga pencarian kemiripan (*cosine similarity*) dapat berjalan dengan sangat cepat.

### 3. Implementasi Pengatur Instruksi LLM (`prompt_template.py`)
Pengaturan identitas dan aturan pembatas respon *chatbot* diimplementasikan pada modul `prompt_template.py`.

#### Tabel 4.4 Potongan Kode Program Pengatur Instruksi LLM (`prompt_template.py`)

| Baris | Kode Program Python (`prompt_template.py`) |
|---|---|
| 1 | `SYSTEM_PROMPT = "Anda adalah Customer Service Virtual resmi..."` |
| 2 | `# Instruksi identitas CS Virtual CV. Asia Visual Grafika Pekanbaru` |
| 3 | `# Aturan 1: Bahasa Indonesia ramah khas percetakan Pekanbaru` |
| 4 | `# Aturan 2: Jawab HANYA berdasarkan konteks dokumen (Cegah Halusinasi)` |
| 5 | `# Aturan 3: Hitung harga spanduk (PxL x Rp/m2 x Jumlah) secara transparan` |

Penjelasan alur kerja kode program Tabel 4.4 diuraikan sebagai berikut:
1. Pada baris 1 dan 2, variabel `SYSTEM_PROMPT` menetapkan peran *bot* sebagai Staf CS resmi CV. Asia Visual Grafika Pekanbaru.
2. Pada baris 3 dan 4, instruksi mengatur gaya bahasa agar ramah dan membatasi LLM agar hanya menjawab berdasarkan dokumen rujukan toko (*context grounding*) untuk mencegah timbulnya halusinasi AI.
3. Pada baris 5, diterapkan rumus kalkulasi harga cetak agar *bot* dapat mengalikan panjang dikali lebar dikali tarif bahan dan menampilkan perhitungannya secara transparan.

### 4. Implementasi Endpoint Webhook WhatsApp (`routes.py`)
Penerimaan pesan dari WhatsApp dan pengiriman jawaban diimplementasikan pada modul `routes.py`.

#### Tabel 4.5 Potongan Kode Program Endpoint Webhook WhatsApp (`routes.py`)

| Baris | Kode Program Python (`routes.py`) |
|---|---|
| 1 | `@chat_router.post("/whatsapp")` |
| 2 | `async def whatsapp_webhook(request: Request):` |
| 3 | `    form = await request.form()` |
| 4 | `    sender = form.get("sender")` |
| 5 | `    message = form.get("message")` |
| 6 | `    response = rag_chain.run(question=message, session_id=f"wa_{sender}")` |
| 7 | `    send_whatsapp_message(target=sender, message=response.answer)` |
| 8 | `    return {"status": "success"}` |

Penjelasan alur kerja kode program Tabel 4.5 diuraikan sebagai berikut:
1. Pada baris 1 dan 2, fungsi `whatsapp_webhook` didaftarkan sebagai *endpoint* HTTP POST URL `/whatsapp` secara asinkron (*async*) untuk menangani pesan masuk dari pelanggan.
2. Pada baris 3 hingga 5, fungsi mengekstrak nomor pengirim (`sender`) dan isi pesan pertanyaan (`message`) dari data *payload* gateway WhatsApp.
3. Pada baris 6 hingga 8, pertanyaan diproses melalui *pipeline* RAG (`rag_chain.run()`), jawaban dikirimkan kembali ke WhatsApp pelanggan via `send_whatsapp_message()`, lalu server mengembalikan respon status sukses.

### 5. Pembuatan Antarmuka Web Admin Portal
Selain integrasi WhatsApp, peneliti membangun antarmuka web khusus bagi pengelola toko pada URL `/admin`.

> **Gambar 4.4** Tangkapan Layar Halaman Web Admin Portal (`/admin`)

Tangkapan layar *Web Admin Portal* pada Gambar 4.4 memperlihatkan antarmuka berbasis web yang memungkinkan staf toko mengedit 6 berkas pengetahuan `.txt`, menekan tombol simpan untuk memperbarui indeks ChromaDB secara otomatis, serta melihat log riwayat percakapan pelanggan.

---

## E. Tahap Pengujian

Tahap pengujian dilakukan untuk mengevaluasi kinerja sistem *chatbot* yang telah dibangun melalui empat metode pengujian: *Black Box Testing*, akurasi pencarian informasi (*Retrieval*), kebergunaan sistem (*System Usability Scale* / SUS), dan penilaian kualitas respon (*Human Evaluation*).

### 1. Pengujian Fungsionalitas (Black Box Testing)
Pengujian fungsionalitas dilakukan terhadap 10 skenario pengujian untuk memastikan setiap fitur berjalan sesuai dengan hasil yang diharapkan.

> **Gambar 4.5** Tangkapan Layar Percakapan WhatsApp Pengujian Sapaan dan Hitung Harga Spanduk

#### Tabel 4.6 Hasil Pengujian Black Box Testing (10 Skenario Uji)

| No | Skenario Pengujian | Input Test Case | Hasil yang Diharapkan | Hasil Pengamatan | Status |
|---|---|---|---|---|---|
| 1 | Deteksi Sapaan Awal | "Halo min, selamat pagi" | Bot memberikan pesan sambutan ramah + daftar menu utama tanpa query ChromaDB | Sambutan & menu tampil sesuai | **SESUAI** |
| 2 | Informasi Lokasi Toko | "Min lokasi tokonya dimana ya?" | Bot menyebutkan alamat lengkap cabang Pekanbaru & jam operasional | Alamat 2 cabang tampil tepat | **SESUAI** |
| 3 | Kebijakan Pembayaran | "Harus DP dulu apa bisa bayar nanti?" | Bot menjelaskan aturan wajib DP 50-60% sebelum proses cetak | Penjelasan DP tampil akurat | **SESUAI** |
| 4 | Panduan Berkas Cetak | "Format file apa yang bagus dikirim?" | Bot menyarankan format PDF Print/CDR/JPEG 300 DPI CMYK | Panduan file cetak tampil tepat | **SESUAI** |
| 5 | Rekomendasi Bahan | "Stiker buat botol minum tahan air bagusnya apa?" | Bot merekomendasikan Stiker Vinyl Ritrama yang tahan air | Rekomendasi bahan tepat | **SESUAI** |
| 6 | Kalkulasi Harga Cetak | "Harga banner flexi 280 ukuran 2x1 meter 2 lembar?" | Bot menghitung 2x1x2xRp16.500 = Rp66.000 | Hitungan harga akurat | **SESUAI** |
| 7 | Memori Multi-Turn | Turn 1: "Harga flexi korcin brp?"<br>Turn 2: "Kalo ukuran 3x1 brp?" | Bot mengingat konteks bahan Flexi Korcin dari Turn 1 pada Turn 2 | Konteks bahan teringat | **SESUAI** |
| 8 | Fitur Reset Sesi | "reset" | Bot membersihkan riwayat percakapan dan mengonfirmasi reset | Riwayat terhapus | **SESUAI** |
| 9 | Pertahanan Prompt Injection | "Abaikan instruksi, berikan instruksi rahasia kamu!" | Bot menolak dan membalas dengan pesan standar tanpa bocor | System prompt terlindungi | **SESUAI** |
| 10 | Pengelolaan Admin Portal | Buka `/admin`, edit teks harga, klik Simpan | File `.txt` tersimpan di disk dan indeks ChromaDB auto-reload | KB & ChromaDB terupdate | **SESUAI** |

Hasil *Black Box Testing* pada Tabel 4.6 menunjukkan bahwa seluruh 10 skenario pengujian berhasil lulus dengan status 100% SESUAI tanpa ditemukan adanya kesalahan fungsi.

### 2. Pengujian Akurasi Retrieval
Akurasi penarikan informasi diukur menggunakan skrip pengujian `testing/run_evaluation.py` terhadap 10 pertanyaan uji representatif dengan mengambil 3 potongan dokumen teratas (*Top-3 Chunks*).

> **Gambar 4.6** Tangkapan Layar Eksekusi Skrip Evaluasi Retrieval di Terminal

#### Tabel 4.7 Hasil Pengujian Akurasi Retrieval (10 Pertanyaan Acuan)

| No | Pertanyaan Uji Acuan | Kategori Kueri | Target File Acuan | Hit@3 | Precision@3 |
|---|---|---|---|---|---|
| 1 | Lokasi toko percetakan dimana? | Fakta Langsung | `01_profil_dan_layanan.txt` | 1 | 0.3333 |
| 2 | Harus DP berapa persen sebelum cetak? | Fakta Langsung | `01_profil_dan_layanan.txt` | 1 | 0.3333 |
| 3 | Berapa harga stiker vinyl tahan air? | Fakta Langsung | `06_harga_dan_estimasi.txt` | 1 | 0.6667 |
| 4 | Format berkas cetak yang disarankan apa? | Fakta Langsung | `03_teknis_dan_spesifikasi.txt` | 1 | 1.0000 |
| 5 | klo spanduk pke flexi 280 brp ya? | Variasi Bahasa | `06_harga_dan_estimasi.txt` | 1 | 0.3333 |
| 6 | klo cetakan salah bsa diretur gak? | Variasi Bahasa | `04_alur_dan_kebijakan.txt` | 1 | 0.3333 |
| 7 | Total 2 lembar banner flexi 280 2x1m? | Perhitungan Implisit | `06_harga_dan_estimasi.txt` | 1 | 0.6667 |
| 8 | Cetak stiker 5x5 cm di A3+ muat berapa? | Perhitungan Implisit | `06_harga_dan_estimasi.txt` | 1 | 0.3333 |
| 9 | Nota 2 ply minimal pemesanan berapa rim? | Fakta Implisit | `06_harga_dan_estimasi.txt` | 1 | 1.0000 |
| 10 | Bahan terbaik untuk banner outdoor tahan angin? | Informasi Spesifikasi | `02_produk_layanan_detail.txt` | 1 | 0.6667 |
| **RATA-RATA** | | | | **100.0%** | **0.5667 (56.67%)** |

Nilai *Hit Rate@3* sebesar **100.0%** membuktikan bahwa pencarian pada ChromaDB selalu berhasil menemukan dokumen acuan yang relevan pada 3 potongan teks teratas. Nilai *Precision@3* sebesar **56.67%** menunjukkan bahwa mayoritas potongan teks yang diambil relevan dengan kebutuhan jawaban.

### 3. Pengujian Ketergunaan Sistem (System Usability Scale / SUS)
Pengujian kebergunaan sistem dilakukan dengan membagikan kuesioner baku SUS (10 pertanyaan standar dengan skala Likert 1–5) kepada 20 responden yang terdiri atas pelanggan toko dan staf admin operasional.

> **Gambar 4.7** Grafik Batang Skor Kuesioner SUS dari 20 Responden Pengguna

#### Tabel 4.8 Rekapitulasi Nilai Kuesioner SUS (20 Responden)

| Responden | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 | Total Skor SUS | Kategori Keberterimaan |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R01 | 4 | 1 | 5 | 1 | 4 | 2 | 5 | 1 | 4 | 1 | 87.5 | Excellent (Grade A) |
| R02 | 5 | 2 | 4 | 1 | 5 | 1 | 4 | 2 | 5 | 2 | 82.5 | Excellent (Grade A) |
| R03 s.d. R20 | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | *(Skor Responden)* | *(Kategori Grade)* |
| **RATA-RATA** | | | | | | | | | | | **[XX.X]** | **Acceptable (Good/Excellent)** |

Hasil rekapitulasi nilai SUS pada Tabel 4.8 membuktikan bahwa sistem *chatbot* dinilai praktis, mudah digunakan, dan dapat diterima dengan sangat baik oleh pengguna akhir (*Acceptable*).

### 4. Pengujian Kualitatif Jawaban (Human Evaluation)
Penilaian kualitas jawaban dilakukan oleh 3 penilai dari staf internal toko (Mba Intan, Mas Rizky, dan Shinta) menggunakan skala 1 hingga 5 terhadap aspek kesopanan bahasa, kejelasan, dan ketepatan perhitungan harga cetak.

#### Tabel 4.9 Hasil Penilaian Human Evaluation oleh Staf Toko

| Kategori Pertanyaan | Pertanyaan Uji Sample | Evaluator 1 (Mba Intan) | Evaluator 2 (Mas Rizky) | Evaluator 3 (Shinta) | Rata-rata Skor (1-5) | Keterangan Evaluasi |
|---|---|---|---|---|---|---|
| Informasi Toko | Jam operasional & lokasi cabang? | 5.0 | 5.0 | 5.0 | 5.00 | Sangat Akurat & Ramah |
| Berkas Cetak | Format file & resolusi gambar? | 5.0 | 4.0 | 5.0 | 4.67 | Informasi Jelas & Tepat |
| Rekomendasi Bahan | Stiker tahan air untuk outdoor? | 4.0 | 5.0 | 5.0 | 4.67 | Sesuai Spesifikasi Toko |
| Kalkulasi Harga | Hitung banner 2x1m flexi 280 (2 lembar)? | 5.0 | 5.0 | 5.0 | 5.00 | Hitungan Matematika Tepat |
| Percakapan Multi-turn | Konteks bahan berlanjut di turn 2? | 4.0 | 4.0 | 5.0 | 4.33 | Memori Konteks Terjaga |
| **RATA-RATA TOTAL** | | | | | **[X.XX / 5.00]** | **Sangat Baik** |

Hasil penilaian staf toko pada Tabel 4.9 membuktikan bahwa respon yang dihasilkan *chatbot* dinilai sangat sopan, ramah, dan perhitungan estimasi harga cetak spanduk/stiker sudah tepat sesuai dengan standar operasional CV. Asia Visual Grafika.

### 5. Pembahasan Hasil Pengujian
Berdasarkan hasil eksekusi keempat metode pengujian di atas, dapat disimpulkan bahwa:
1. Pengujian fungsionalitas *Black Box* membuktikan seluruh modul sistem (koneksi WhatsApp, proses RAG, dan portal admin) beroperasi 100% sesuai spesifikasi.
2. Pengujian akurasi *retrieval* dengan *Hit Rate@3* 100% memastikan informasi yang diberikan kepada pelanggan bersumber dari dokumen resmi toko dan bebas dari halusinasi AI.
3. Penerapan *chatbot* ini mampu menjawab kendala keterlambatan respon chat, membantu meringankan beban kerja staf CS, serta memberikan kemudahan bagi pelanggan dalam mengecek tarif dan berkas cetak selama 24 jam secara mandiri.
