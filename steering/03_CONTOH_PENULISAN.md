# 03_CONTOH_PENULISAN.md — Draf & Referensi Naskah Utuh Skripsi

> 🛑 **PERINGATAN SANGAT PENTING (BACA INI):**
> File ini berisi **CONTOH TEMPLATE FORMAT PENULISAN** dari sampel skripsi lain (Studi Kasus: PT Finnet / IT Support).
> **DILARANG KERAS** mengambil objek, angka metrik (seperti RAGAs, LLaMA, FAISS, atau PT Finnet) dari file ini untuk skripsi Anda!
> 
> **ACUAN MUTLAK SKRIPSI ANDA (CV. ASIA VISUAL GRAFIKA):**
> 1. Objek: **CV. Asia Visual Grafika** (Percetakan Pekanbaru, Mas Aji Owner).
> 2. Platform: **WhatsApp Webhook API**.
> 3. Database & Model: **ChromaDB** + **`intfloat/multilingual-e5-small`** + **Google Gemini 2.5 Flash**.
> 4. Knowledge Base: **6 File `.txt`** (`01_` s.d. `06_`).
> 5. 4 Metrik Pengujian Resmi Bab V:
>    - **Black Box Testing** (10 Skenario Fungsionalitas)
>    - **Akurasi Retrieval** (Hit Rate@3 = 100.0%, Precision@3 = 56.67% pada 10 pertanyaan acuan via `run_evaluation.py`)
>    - **System Usability Scale (SUS)** (Kuesioner 10 pertanyaan pada 20 responden)
>    - **Human Evaluation** (Penilaian kualitatif kesopanan, kelayakan, & ketepatan hitungan harga)
>
> 📌 *Gunakan file ini HANYA sebagai acuan gaya bahasa dan struktur paragraf, BUKAN isi datanya.*

## "Implementasi Chatbot Informasi Usaha Percetakan Menggunakan Retrieval-Augmented Generation (Studi Kasus: CV. Asia Visual Grafika)"

**Penulis**: Mohammad Riza Al Fahrie (NIM: 11220910000057)  
**Program Studi**: Teknik Informatika, Fakultas Sains dan Teknologi, UIN Syarif Hidayatullah Jakarta  
**Tahun**: 2026 M / 1448 H  
**Tanggal Sidang Munaqasyah**: 11 Agustus 2026  
**Dosen Pembimbing 1**: Fitri Mintarsih, M.Kom. (NIP. 197212232007102004)  
**Dosen Pembimbing 2**: Juri Pebrianto, S.Kom., M.Kom. (NIP. 199002092025051001)  
**Penguji 1**: Ir. Nashrul Hakiem, S.Si., M.T., Ph.D. (NIP. 197106082005011005)  
**Penguji 2**: Muhammad Sobri, M.Kom., Ph.D. (NIP. 198808182025051001)  
**Dekan FST**: Prof. Husni Teja Sukmana, S.T., M.Sc., Ph.D.  
**Ketua Program Studi**: Dr. Dewi Khairani, S.Kom., M.Sc.  

---

## ABSTRAK

**Bahasa Indonesia:**
Perkembangan Large Language Model (LLM) mendorong pemanfaatan chatbot, tetapi masalah seperti halusinasi dapat menurunkan akurasi jawaban. Penelitian ini mengimplementasikan Chatbot IT Support berbasis Retrieval-Augmented Generation (RAG) untuk membantu troubleshooting karyawan dengan knowledge base internal perusahaan. Chatbot memakai Gemini 2.5 Flash, Llama 3.1 8B Instant, dan Qwen3 8B. Kemudian, performa ketiga model tersebut dibandingkan menggunakan RAGAs dan human evaluation. Pada proses retrieval dilakukan juga pengoptimalan similarity threshold. Sementara itu, black box testing digunakan untuk menguji fungsionalitas sistem. Hasil menunjukkan bahwa seluruh fungsi sistem berjalan dengan baik berdasarkan black box testing. Llama 3.1 8B Instant memberikan performa terbaik dengan rata-rata latency 882,26 ms, penggunaan 1.068,7 token, dan kualitas jawaban dengan nilai human evaluation 4,44 dari 5. Pada RAGAs, LLaMA memperoleh nilai tertinggi dibandingkan model lainnya dengan faithfulness 0,9667 dan answer relevancy 0,8074. Nilai similarity threshold 0,50 menghasilkan tingkat keberhasilan retrieval sebesar 100% dengan rata-rata 2,9 dokumen sebagai konteks. Dengan demikian, LLaMA 3.1 8B Instant dan similarity threshold 0,50 merupakan konfigurasi yang paling sesuai untuk Chatbot IT Support dalam membantu troubleshooting karyawan.

**Kata Kunci**: Chatbot, Retrieval-Augmented Generation, IT Support, Large Language Model, Similarity Threshold

---

## BAB I: PENDAHULUAN

### A. Latar Belakang
Dalam era digital saat ini, pengelolaan layanan teknologi informasi menjadi salah satu aspek penting dalam mendukung aktivitas operasional perusahaan. Layanan teknologi seperti printer, laptop, Microsoft 365 dan aplikasi pendukung lainnya merupakan bagian integral dari operasional perusahaan yang harus dikelola secara terstruktur dan berkelanjutan. Ketersediaan layanan tersebut digunakan untuk menunjang berbagai aktivitas kerja karyawan. Seiring dengan meningkatnya ketergantungan perusahaan terhadap teknologi informasi, kebutuhan akan layanan IT Support yang mampu memberikan dukungan teknis secara cepat, tepat, dan berkelanjutan juga semakin meningkat (Ulmer, 2025).
Penggunaan teknologi informasi yang semakin meningkat menyebabkan jumlah permintaan layanan teknis dari pengguna juga terus bertambah. Permasalahan yang sering muncul meliputi gangguan pada perangkat keras, aplikasi, sistem operasi, akun pengguna, dan layanan digital perusahaan. Di sisi lain, prosedur operasional, panduan troubleshooting, dan dokumentasi teknis umumnya tersimpan pada berbagai media yang berbeda, seperti dokumen SOP, FAQ, dan email. Kondisi tersebut menyebabkan proses pencarian informasi menjadi kurang efisien karena pengguna atau staf membuka berbagai sumber informasi yang terpisah. Akibatnya, penyelesaian masalah menjadi lebih lama dan beban kerja tim IT Support semakin meningkat (Toro Isaza et al., 2025).
Untuk mengatasi permasalahan tersebut, dibutuhkan sistem yang mampu membantu proses digitalisasi layanan IT Support secara terintegrasi dan efisien. Salah satu teknologi yang dapat diterapkan adalah chatbot berbasis Artificial Intelligence (AI). Chatbot AI mampu membantu proses otomatisasi layanan dengan memberikan respons cepat terhadap pertanyaan dan kendala teknis yang dialami pengguna. Teknologi ini memicu pengguna berinteraksi memakai bahasa alami sehingga proses konsultasi atau pencarian solusi menjadi lebih praktis dan efisien. Pada implementasi layanan IT Support, chatbot dapat dimanfaatkan untuk menjawab pertanyaan,
2
memberikan panduan troubleshooting, membantu pencarian solusi dari dokumentasi perusahaan, hingga mengurangi beban kerja dalam menangani permasalahan repetitif (Dea & Darmawan, 2024).
Dalam pengembangan chatbot berbasis AI, terdapat beberapa pendekatan yang umum digunakan seperti Large Language Model (LLM), fine-tuning, dan Retrieval-Augmented Generation (RAG). Menurut (Hsueh & Lin, 2026) penggunaan LLM standar memiliki kelemahan utama berupa kecenderungan menghasilkan informasi yang tidak akurat atau halusinasi karena model tidak memiliki konteks spesifik terkait prosedur internal perusahaan. Selain itu, metode fine-tuning pada LLM membutuhkan biaya komputasi yang tinggi, waktu pelatihan yang lama, dan proses pemeliharaan yang kompleks ketika terdapat perubahan dokumentasi knowledge base perusahaan. Kondisi tersebut berpotensi menyebabkan jawaban chatbot tidak sesuai dengan prosedur operasional perusahaan.
Sementara itu, Retrieval-Augmented Generation (RAG) termasuk pendekatan yang menggabungkan kemampuan Large Language Model (LLM) menggunakan sistem information retrieval dari knowledge base eksternal terhadap model, seperti dokumen pdf, database, atau website. Menurut (Cheng et al., 2025), pendekatan RAG mampu mengurangi risiko halusinasi karena jawaban yang dihasilkan didasarkan pada data dan dokumen aktual perusahaan. Selain itu, RAG memicu sistem memberikan informasi yang lebih relevan, kontekstual, dan mudah diperbarui tanpa perlu melatih ulang model secara keseluruhan. Dengan pendekatan ini, chatbot dapat memanfaatkan dokumen internal perusahaan, seperti SOP, FAQ, dan panduan troubleshooting lainnya sebagai knowledge base dalam memberikan jawaban kepada pengguna.
Meskipun RAG mampu meningkatkan relevansi informasi dengan memanfaatkan dokumen eksternal, kualitas jawaban yang dihasilkan tetap dipengaruhi oleh konfigurasi pada proses retrieval dan generation. Parameter seperti chunk size, chunk overlap, top-k, similarity threshold, dan konfigurasi prompt dapat memengaruhi relevansi konteks yang diberikan kepada Large Language Model (LLM). Oleh karena itu, implementasi RAG perlu melalui proses evaluasi untuk mengetahui kualitas retrieval, respons yang akan dihasilkan, dan menentukan konfigurasi yang paling optimal sesuai dengan kebutuhan chatbot (Radeva et al., 2024).
3
PT Finnet Indonesia merupakan anak perusahaan dari Telkom Metra (Telkom Group) yang bergerak di bidang teknologi finansial atau fintech yang memberikan layanan jasa keuangan. PT Finnet Indonesia mulai beroperasi sejak tahun 2006 dengan umbrella brand yang dimilikinya yaitu Finpay sebagai penyedia layanan teknologi keuangan, seperti pembayaran digital, payment, gateway, dan switching (Finpay, 2026). Dalam menjalankan operasional, PT Finnet Indonesia memiliki beberapa divisi seperti Information Technology Planning & Governance, Cyber Security, Development, dan lain-lain (Fadiyah, 2025).
Berdasarkan hasil wawancara dengan karyawan System Engineer unit CTO pada tanggal 9 Juli 2026 (rujuk lampiran 3), Corporate Technology Operation (CTO) merupakan salah satu unit di bawah divisi IT Strategy & Corporate Technology (ISCT) PT Finnet Indonesia yang bertanggung jawab dalam pengelolaan layanan teknologi informasi dan dukungan teknis bagi karyawan. Layanan yang dikelola meliputi perangkat laptop, printer, Microsoft 365, Tableau, Pentaho, IT Helpdesk, dan beberapa aplikasi internal perusahaan. Salah satu subunit CTO yaitu IT Support menerima sekitar belasan hingga dua puluh permintaan layanan setiap hari yang meliputi kendala email, printer, Microsoft 365, Windows, instalasi aplikasi, dan panduan troubleshooting dasar perangkat laptop dan sistem operasi Windows.
Hasil wawancara (rujuk lampiran 3) juga menunjukkan selain tingginya jumlah permintaan layanan, prosedur operasional, panduan troubleshooting, dan kebijakan internal masih tersebar pada berbagai dokumen, seperti Standard Operating Procedure (SOP), Frequently Asked Questions (FAQ), International Organization for Standardization (ISO), Minutes of Meeting (MoM), SharePoint, dan email. Kondisi tersebut menyebabkan proses pencarian informasi menjadi kurang efisien karena pengguna harus membuka beberapa sumber informasi yang berbeda. Di sisi lain, jumlah personel CTO yang relatif sedikit dibandingkan dengan banyaknya layanan yang dikelola menyebabkan kebutuhan sistem yang mampu membantu penyampaian informasi secara otomatis semakin meningkat. Oleh karena itu, diperlukan Chatbot IT Support berbasis RAG yang mampu memahami pertanyaan pengguna dan memberikan jawaban yang akurat dari dokumen internal perusahaan.
4
Dari latar belakang tersebut, penulis tertarik untuk melakukan penelitian dengan judul “IMPLEMENTASI CHATBOT IT SUPPORT MENGGUNAKAN RETRIEVAL-AUGMENTED GENERATION UNTUK TROUBLESHOOTING KARYAWAN (Studi Kasus: PT Finnet Indonesia)”. Sistem chatbot akan dikembangkan dengan pendekatan RAG yang mengintegrasikan frontend, backend, vector database, knowledge base, dan LLM. Melalui pendekatan tersebut, chatbot diharapkan mampu menyajikan informasi yang relevan sesuai dokumen internal perusahaan dan mendukung proses troubleshooting karyawan untuk mengurangi beban kerja tim IT Support. Penelitian ini juga mengevaluasi kinerja LLM dan proses retrieval untuk memperoleh konfigurasi yang sesuai dengan kebutuhan Chatbot IT Support di PT Finnet Indonesia.”

### B. Identifikasi Masalah
1. Belum tersedianya chatbot otomatisasi troubleshooting terintegrasi berbasis dokumentasi resmi PT Finnet Indonesia.
2. Belum diketahuinya komparasi kinerja LLM (Gemini 2.5 Flash, LLaMA 3.1 8B Instant, dan Qwen3 8B) pada aspek latency, token usage, serta kualitas jawaban (RAGAs & human evaluation).
3. Belum dioptimalkannya nilai similarity threshold pada tahap retrieval untuk menyaring dokumen relevan dan mencegah halusinasi.

### C. Rumusan Masalah
1. Seberapa baik fungsionalitas Chatbot IT Support dalam memberikan solusi troubleshooting karyawan di PT Finnet Indonesia?
2. Seberapa baik kinerja Large Language Model (LLM) yang digunakan dalam Chatbot IT Support berdasarkan latency, token usage, dan kualitas jawaban yang dievaluasi menggunakan RAGAs dan human evaluation?
3. Seberapa baik nilai similarity threshold dalam mengoptimalkan proses retrieval pada Chatbot IT Support berbasis Retrieval-Augmented Generation (RAG)?

### D. Batasan Masalah
- **Metode**: Studi literatur, observasi langsung di CTO Finnet, wawancara, serta pengembangan Chatbot IT Support berbasis RAG.
- **Tools**:
  - Backend: Python 3.10 & FastAPI.
  - Frontend: TypeScript & ReactJS v19.2 (Tailwind CSS, Vite).
  - LLM & Provider: Gemini 2.5 Flash (Gemini API), LLaMA 3.1 8B Instant (Groq API), Qwen3 8B (Hugging Face API).
  - Vector DB & Embedding: FAISS (Facebook AI Similarity Search) dengan Sentence Transformer (SBERT) all-MiniLM-L6-v2 (384 dimensi).
  - Database Relasional: MySQL (menyimpan riwayat chat & umpan balik pengguna).
  - Evaluasi & Repositori: RAGAs framework, Google Forms (Human Evaluation), GitHub.
  - Dataset Pendukung: IT Helpdesk Tickets dari Hugging Face.
- **Proses**: Indexing, Retrieval, Augmentation, Generation, evaluasi Black Box Testing, RAGAs, Human Evaluation, optimasi Similarity Threshold, dan pengujian Out of Scope.

### E. Tujuan Penelitian
1. Mengimplementasikan Chatbot IT Support berbasis RAG menggunakan knowledge base dokumen internal PT Finnet Indonesia.
2. Mengevaluasi kinerja LLM (Gemini 2.5 Flash, LLaMA 3.1 8B, Qwen3 8B) berdasarkan latency, token usage, RAGAs, dan human evaluation.
3. Mengoptimalkan nilai similarity threshold pada proses retrieval untuk meminimalkan halusinasi.

---

## BAB II: LANDASAN TEORI

### A. Chatbot & Large Language Models (LLMs)
- **Chatbot**: Terbagi menjadi rule-based (kaku, berbasis kata kunci), retrieval-based, dan generative-based (berbasis LLM/Transformer).
- **Arsitektur Transformer**: Dikembangkan atas 3 komponen utama: Tokenisasi, Positional Encoding, dan Multi-Head Attention Mechanism.
- **Closed-Source vs Open-Source LLMs**: Gemini 2.5 Flash (closed-source, Google), LLaMA 3.1 8B Instant (open-source, Meta AI via Groq), Qwen3 8B (open-source, Alibaba Cloud via Hugging Face).

### B. Retrieval-Augmented Generation (RAG)
Diusulkan pertama kali oleh **Lewis et al. (2020)**. RAG memadukan komponen retriever (pencarian dokumen eksternal) dengan generator (LLM) untuk memberikan jawaban faktual berbasis fakta mutakhir (source of truth) tanpa retraining.

### C. Vector Embedding & Vector Database
- **Dense Embedding**: SBERT (all-MiniLM-L6-v2) memetakan teks menjadi vektor numerik padat berdimensi 384 yang menangkap hubungan semantik.
- **FAISS (Facebook AI Similarity Search)**: Pangkalan data vektor untuk melakukan pencarian Approximate Nearest Neighbor (ANN) berkecepatan tinggi.
- **Cosine Similarity**: Metrik pengukur jarak sudut antara dua vektor A (kueri) dan B (dokumen) pada rentang [0, 1]:
  cos(theta) = (A . B) / (||A|| * ||B||)

### D. Framework & Evaluasi
- **Agile Software Development**: Plan, Design, Develop, Test, Deploy, Review, Launch.
- **UML**: Use Case Diagram & Activity Diagram.
- **Black Box Testing**: Pengujian fungsionalitas input-output tanpa memeriksa struktur kode internal.
- **Human Evaluation**: Skala Likert 1-5 berdasarkan aspek Relevansi (Honesty), Kelengkapan (Completeness), dan Kejelasan (Correctness).
- **RAGAs Framework**: Evaluasi otomatis tanpa referensi manusia mencakup Faithfulness, Answer Relevance, dan Context Relevance.
- **Similarity Threshold**: Nilai batas minimum kelayakan skor kemiripan dokumen.

---

## BAB III: METODOLOGI PENELITIAN

### A. Jenis & Objek Penelitian
- **Pendekatan**: Mixed Methods (Kualitatif melalui observasi dan wawancara; Kuantitatif melalui benchmark LLM, RAGAs, dan similarity threshold).
- **Lokasi Objek**: PT Finnet Indonesia, Telkom Landmark Tower Lt. 28, Jl. Gatot Subroto Kav. 52, Jakarta Selatan.

### B. Pengumpulan Data
- **Observasi**: Dilakukan sejak awal Januari 2026 di unit CTO PT Finnet Indonesia.
- **Wawancara**: Dilaksanakan pada 9 Juli 2026 bersama Bapak Husni Ramdani (System Engineer unit CTO).

### C. Contoh Perhitungan Cosine Similarity
Simulasi matematis pada vektor sederhana 2 dimensi:
A = [1, 2], B = [2, 3]
1. Dot Product: A . B = (1 * 2) + (2 * 3) = 2 + 6 = 8
2. Norma Vektor: ||A|| = sqrt(1^2 + 2^2) = sqrt(5) = 2.236, ||B|| = sqrt(2^2 + 3^2) = sqrt(13) = 3.606
3. Cosine Similarity: cos(theta) = 8 / (2.236 * 3.606) = 8 / 8.063 = 0.992

Pada sistem nyata, A dan B berdimensi 384 dari model all-MiniLM-L6-v2.

---

## BAB IV: ANALISIS DAN IMPLEMENTASI

### A. Pengelompokan Knowledge Base
Terdiri dari 10 dokumen internal + dataset Hugging Face yang dikelompokkan ke dalam 6 folder:
1. Microsoft 365: Panduan registrasi MFA, Office 365 MacOS.
2. Network: Panduan VPN GlobalProtect, troubleshooting jaringan.
3. Printer: Instalasi driver Fuji Xerox ApeosPort-VI C3371.
4. Windows 11: Setup BIOS, Troubleshooting Drive Tidak Muncul.
5. IT Helpdesk: Tiket bantuan teknis umum dari Hugging Face.
6. Out of Scope: Dokumen non-IT (misal resep-bakwan.txt) untuk menguji batas sistem.

### B. Arsitektur REST API (FastAPI)
- **Chatbot**: GET /health, POST /chat, GET /suggestions
- **Auth**: POST /auth/register, POST /auth/login
- **Admin**: POST /admin/rebuild-index, POST /admin/upload-document, GET /admin/folders, GET /admin/documents, DELETE /admin/documents/{folder}/{filename}

### C. Kode Program Fungsional RAG

```python
# Preprocessing & Text Chunking
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["

", "
", " ", ""]
)
chunks = splitter.split_text(text)

# Filtering & Augmentation (RAGService)
top_score = results[0]["similarity_score"]
if top_score < settings.SIMILARITY_THRESHOLD: # 0.50
    return fallback_response("Maaf, informasi belum tersedia...")

# Filter dokumen dengan toleransi selisih 0.15
results = [
    item for item in results 
    if item["similarity_score"] >= max(settings.SIMILARITY_THRESHOLD, top_score - 0.15)
]
```

### D. System Message Prompt Template
```text
SYSTEM_MESSAGE = """
Anda adalah chatbot IT Support untuk membantu karyawan PT Finnet Indonesia.
Tugas Anda:
1. Jawab pertanyaan pengguna hanya berdasarkan konteks knowledge base yang diberikan.
2. Jangan menghasilkan informasi di luar konteks knowledge base yang diberikan.
3. Jika informasi tidak tersedia dalam konteks, jawab bahwa informasi belum tersedia di knowledge base.
4. Berikan jawaban dalam bahasa Indonesia.
5. Jika pertanyaan adalah panduan teknis atau troubleshooting, berikan jawaban dalam format Markdown numbered list dengan numbering: 1., 2., 3., dst.
6. Pastikan setiap langkah dimulai dengan angka dan titik (contoh: "1. Buka portal...").
7. Jawaban harus ringkas, jelas, dan mudah diikuti oleh karyawan non-teknis.

=== KONTEKS KNOWLEDGE BASE ===
{context}

=== PERTANYAAN PENGGUNA ===
{query}

=== JAWABAN ===
""".strip()
```

---

## BAB V: HASIL DAN PEMBAHASAN

### A. Hasil Black Box Testing
8 Skenario Pengujian (Login Admin, Upload KB, Delete KB, Pilih Provider, Pilih LLM, Kirim Kueri, Retrieval & Generasi, Akses Sumber Output) dinyatakan **100% BERHASIL**.

### B. Hasil Benchmark 3 Model LLM (10 Sampel Pertanyaan)

| Metrik Evaluasi | Gemini 2.5 Flash | LLaMA 3.1 8B Instant | Qwen3 8B | Model Terbaik |
| :--- | :---: | :---: | :---: | :---: |
| **Rata-rata Latency (ms)** | 3.792,81 | **882,26** | 4.361,40 | **LLaMA 3.1 8B** (Tercepat) |
| **Rata-rata Token Usage** | 1.238,6 | **1.068,7** | 1.387,0 | **LLaMA 3.1 8B** (Paling Hemat) |
| **RAGAs - Faithfulness** | 0,9150 | **0,9667** | 0,8720 | **LLaMA 3.1 8B** |
| **RAGAs - Answer Relevance** | 0,7518 | **0,8074** | 0,5845 | **LLaMA 3.1 8B** |
| **RAGAs - Context Relevance**| 0,9417 | 0,9472 | **0,9599** | **Qwen3 8B** |
| **Human Eval - Relevansi** | 4,00 | **4,67** | 4,00 | **LLaMA 3.1 8B** |
| **Human Eval - Kelengkapan**| 3,67 | **4,33** | **4,33** | **LLaMA & Qwen** |
| **Human Eval - Kejelasan** | 3,67 | 4,33 | **4,67** | **Qwen3 8B** |
| **Human Eval - Overall Mean**| 3,78 | **4,44** | 4,33 | **LLaMA 3.1 8B** (Unggul Mutlak) |

### C. Hasil Pengujian Optimasi Similarity Threshold (Model LLaMA 3.1 8B)

| Nilai Threshold | Rata-rata File Diretrieval | Retrieval Berhasil | Jumlah Fallback | Tingkat Keberhasilan | Status Evaluasi |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **0,30** | 4,8 dokumen | 10 | 0 | 100% | Konteks terlalu padat/berlebih |
| **0,40** | 3,7 dokumen | 10 | 0 | 100% | Konteks masih terlampau luas |
| **0,50** | **2,9 dokumen** | **10** | **0** | **100%** | **OPTIMAL** (Efisien & Presisi) |
| **0,60** | 1,6 dokumen | 9 | 1 | 90% | Mulai timbul fallback |
| **0,70** | 0,8 dokumen | 5 | 5 | 50% | Terlalu ketat (fallback 50%) |

---

## BAB VI: KESIMPULAN DAN SARAN

### A. Kesimpulan
1. Sistem Chatbot IT Support berbasis RAG terbukti memenuhi seluruh kebutuhan fungsional (100% lulus Black Box Testing) dalam menjawab kendala karyawan sesuai knowledge base internal PT Finnet Indonesia.
2. **LLaMA 3.1 8B Instant (via Groq)** terbukti sebagai model LLM terbaik di antara ketiga model (latency tercepat 882,26 ms, penggunaan token paling hemat 1.068,7, skor Human Evaluation tertinggi 4,44/5, serta skor RAGAs Faithfulness 0,9667 dan Answer Relevance 0,8074).
3. Nilai similarity threshold sebesar **0,50** merupakan konfigurasi retrieval paling optimal yang menjaga tingkat keberhasilan pencarian tetap 100% tanpa timbul fallback.

### B. Saran
1. Memperkaya knowledge base dengan dokumen troubleshooting yang lebih luas.
2. Mengembangkan kemampuan pemrosesan dokumen bergambar/diagram (multimodal/OCR).
3. Menguji variasi parameter RAG lain seperti chunk size, chunk overlap, dan top-k.
4. Mengintegrasikan chatbot secara langsung ke portal web CTO PT Finnet Indonesia.
5. Menambahkan dukungan multi-language (Inggris, Mandarin, dll.).
6. Menambahkan fitur pembanding jawaban dua model LLM secara berdampingan (side-by-side).

---

## LAMPIRAN: TRANSKRIP WAWANCARA UTUH

**Narasumber**: Bapak Husni Ramdani (System Engineer CTO PT Finnet Indonesia)  
**Waktu & Tempat**: Kamis, 9 Juli 2026 (11.00 - 12.00 WIB), Telkom Landmark Tower Lt. 7  

- **Peneliti**: "Permasalahan apa yang mendorong perlunya implementasi chatbot di PT Finnet Indonesia?"
- **Narasumber**: "Prosedur dan kebijakan perusahaan untuk aplikasi internal masih tersebar di beberapa media seperti SharePoint dan email. Saya membutuhkan satu aplikasi yang mengintegrasikan seluruh informasi tersebut. Saya membawahi pengelolaan layanan IT Support yang mencakup laptop, printer, Microsoft, Tableau, Pentaho, hingga IT Helpdesk. Jumlah tim saya relatif sedikit, sementara portofolio yang dikelola cukup banyak."
- **Peneliti**: "Dalam satu hari, berapa rata-rata permintaan atau permasalahan yang diterima?"
- **Narasumber**: "Dalam satu hari berkisar antara belasan hingga sekitar dua puluh permintaan."
- **Peneliti**: "Dokumen apa saja yang dapat dijadikan knowledge base?"
- **Narasumber**: "Dokumen SOP, FAQ, ISO, dan notulen rapat (MoM). Saya menginginkan agar setiap dokumen dilengkapi tautan menuju sumber lain seperti Google atau YouTube."
- **Peneliti**: "Apakah dokumen tersebut bersifat sensitif?"
- **Narasumber**: "Dokumen operasional CTO bukan merupakan dokumen rahasia perusahaan, melainkan panduan instalasi printer, Microsoft 365, dan Tableau."
- **Peneliti**: "Apa harapan setelah chatbot ini dikembangkan?"
- **Narasumber**: "Harapannya dapat mempercepat akses informasi, mengurangi waktu pencarian dokumen, dan mengurangi beban kerja tim CTO."

# STRUKTUR SISTEMATIKA SKRIPSI
BAB III Metode Penelitian
A. Metode Pengumpulan Data
   1. Data Primer
   2. Data Sekunder
B. Metode Pengembangan Sistem (Prototyping)
   1. Tahap Komunikasi
   2. Tahap Perencanaan Cepat
   3. Tahap Pemodelan Cepat
   4. Tahap Kontruksi
   5. Tahap Pengujian
BAB IV Analisis, Perancangan, Implementasi, Dan Pengujian Sistem
   1. Tahap Komunikasi
   2. Tahap Perencanaan Cepat
      a. Analisis Masalah dan Sistem Berjalan
      b. Analisis Kebutuhan Fungsional Sistem
   3. Tahap Pemodelan Cepat
      a. Pembuatan Knowledge Base
      b. Arsitektur Chatbot
      e. Pembuatan Antarmuka
   4. Tahap Kontruksi
      a.Penyusunan Knowledge Base
      b.Pembuatan Alur RAG
      c.Pembuatan Antarmuka
   5. Tahap Pengujian Sistem         
BAB V HASIL DAN PEMBAHASAN
   1. Hasil Pengujian Pencarian Dokumen
   2. Hasil Pengukuran Model LLM
   3. Hasil Kuisioner SUS
   4. Pembahasan
BAB VI KESIMPULAN DAN SARAN
   1. Kesimpulan
   2. Saran



