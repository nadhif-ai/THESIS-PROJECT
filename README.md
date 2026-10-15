# Chatbot Asia Visual Grafika — RAG + WhatsApp

Chatbot informasi percetakan untuk satu bisnis. Pelanggan menggunakan WhatsApp melalui Fonnte; administrator mengelola dokumen, menguji jawaban, mengatur model, dan melihat evaluasi di dashboard React + shadcn.

Pipeline yang sama dipakai WhatsApp, playground, dan evaluasi: embedding E5 lokal → pencarian Pinecone → jawaban OpenRouter. LangSmith menyimpan trace dan hasil eksperimen; DeepEval menghitung metrik kualitas. Chatbot memberikan informasi; pemesanan dan pembayaran tetap ditangani admin toko.

## Menjalankan di macOS

Gunakan Python **3.12** dan Node **22.12+**. Jalankan perintah dari root proyek:

```bash
uv venv --python 3.12 venv
uv pip install --python venv/bin/python -r requirements.txt
```

Untuk membuat environment baru, salin `.env.example` menjadi `.env` lalu isi kredensial. Jika `.env` sudah ada, gunakan file tersebut.

Unduh embedding sekali jika belum ada di cache:

```bash
HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 venv/bin/python -c "from app.backend.models import get_embedding_model; get_embedding_model()"
```

Build dashboard:

```bash
cd frontend
npm ci
npm run build
cd ..
```

Mulai backend:

```bash
venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Buka [dashboard admin](http://127.0.0.1:8000/admin/) atau [API docs](http://127.0.0.1:8000/docs). State administrasi harus dimigrasikan terlebih dahulu mengikuti [runbook Supabase](docs/runbooks/supabase-state-cutover.md). Akun, hash password, dan sesi lama dipertahankan; startup tidak membuat akun atau mengimpor data secara otomatis. Kredensial lama tetap berlaku.

Untuk development frontend, jalankan `npm run dev` dari `frontend/` di terminal kedua dan buka [Vite admin](http://127.0.0.1:5173/admin/). Permintaan admin API diteruskan ke backend port 8000.

## Konfigurasi

| Variabel | Keterangan |
| --- | --- |
| `PINECONE_API_KEY`, `PINECONE_INDEX_NAME` | Indeks vector dense **384 dimensi, cosine** |
| `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` | Provider dan model pemberi jawaban |
| `EVAL_MODEL` | Model judge terpisah; default `google/gemini-2.5-flash` |
| `SEMANTIC_TOP_K` | Jumlah passage untuk jawaban; dapat diubah di Providers |
| `LANGSMITH_TRACING`, `LANGSMITH_ENDPOINT`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` | Trace dan laporan evaluasi |
| `LANGSMITH_WORKSPACE_ID` | Opsional jika key LangSmith memerlukan workspace organisasi |
| `FONNTE_TOKEN` | Pengiriman balasan WhatsApp |
| `DATABASE_URL` | Koneksi PostgreSQL runtime dengan role terbatas `chatbot_app` |
| `DATABASE_MIGRATION_URL` | Koneksi operator untuk migrasi eksplisit; tidak dipakai runtime |
| `DATA_DIR` | Berkas knowledge, artefak evaluasi, dan backup lokal; default `./data` |
| `COOKIE_SECURE`, `ALLOWED_ORIGINS` | Cookie dan origin untuk lingkungan HTTPS atau origin tambahan |

Kunci tidak dikirim ke browser. Pengaturan model dan retrieval disimpan di PostgreSQL; nilai dashboard yang telah disimpan memiliki prioritas terhadap default `.env`. Embedding tetap `intfloat/multilingual-e5-small` untuk perbandingan migrasi. Pergantian embedding memerlukan indeks yang kompatibel dan reindex.

## Menggunakan dashboard

1. **Dashboard**: status knowledge, aktivitas, waktu respons, dan baseline retrieval.
2. **Knowledge**: pilih versi, buat draft, upload/edit dokumen TXT/MD/PDF/CSV, lalu index. PDF harus memiliki teks; OCR belum tersedia.
   Di **Passage configuration**, simpan ukuran chunk dan overlap sebelum indexing. Draft dari versi lama dimulai dengan **1.000 karakter / overlap 100**. Pengaturan disimpan per versi; versi ready/published harus diklon menjadi draft untuk mengubahnya. Indexing mempertahankan heading produk pada tiap passage, menghapus separator kosong, dan menolak passage di atas batas **512 token E5** agar teks tidak terpotong diam-diam. Nilai karakter tidak sama dengan token.
3. **Playground**: pilih versi published atau ready, ajukan pertanyaan, lihat konteks/sumber, penggunaan token, dan link trace LangSmith. Sesi playground terpisah dari pelanggan.
4. Setelah review, **Publish to WhatsApp** mengaktifkan versi ready. Pilih versi ready sebelumnya dan publish untuk rollback. File gagal diindex tidak mengganti knowledge pelanggan.
5. **Conversations**: filter WhatsApp, playground, API, atau evaluasi. Riwayat lama diimpor sekali tanpa mengubah file asal.
6. **Providers**: model jawaban, model judge, top-k, dan status konfigurasi kredensial.
7. **Evaluations**: jalankan pertanyaan asli atau skenario percakapan yang telah direview; periksa skor/alasan per kasus, ekspor JSON, dan buka eksperimen LangSmith.

Job indexing dan evaluasi berjalan dengan satu worker lokal. Status dan hasil disimpan; startup mempertahankan status pekerjaan yang terputus. Periksa proses pemilik dan hasilnya sebelum melakukan pemulihan manual. Kegagalan upload hasil LangSmith dapat di-retry memakai skor tersimpan tanpa memanggil judge lagi.

## Baseline dan evaluasi

Baseline Chroma tersimpan di `testing/baselines/2026-10-12-chroma/`: 10 pertanyaan, 95 passage beserta vector, snapshot source, konfigurasi dan checksum. Hit Rate@3 **90%**, source-file Precision@3 **60%**. Jawaban asli beserta konteks dan trace juga disimpan sebelum mengganti retriever.

Perbandingan Pinecone:

```bash
HF_HUB_DISABLE_PROGRESS_BARS=1 venv/bin/python -m testing.compare_retrieval
```

Metrik lama adalah pencocokan nama source file pada k=3; runtime jawaban saat capture menggunakan k=5. Jangan menafsirkan skor retrieval sebagai akurasi jawaban.

### Review referensi dan eksperimen chunking

DeepEval QA sekarang menghitung **Contextual Precision** dan **Contextual Recall** selain Faithfulness, Answer Relevancy, dan Business Correctness. Skor retrieval lama tetap terpisah. Hasil run menyimpan konfigurasi chunking, hash corpus, hash dataset, model/judge, dan top-k; model jawaban, judge dan top-k dibekukan selama satu run.

Di **Evaluations → QA reference review**, periksa `testing/evals/qa-reference-candidates.json`. Kandidat ini berasal dari 10 pertanyaan asli, dengan catatan fakta wajib/opsional dan klarifikasi yang diterima. **Kasus 8 sudah dikonfirmasi: Kiss Cut 5×5 cm = 35 pcs per lembar A3+**; hold dilepas dan 10 kasus tersedia setelah admin menandai referensinya reviewed. Referensi QA saat ini juga diperbarui; baseline historis tetap utuh. Perubahan isi membatalkan review. Review percakapan dan review QA merupakan dua status terpisah.

Konteks kandidat percakapan lama mengandung tabel Kiss Cut yang sudah digantikan. Dataset itu ditandai stale dan tidak dapat ditandai reviewed sebelum konteks/outcome dikoreksi atau dibuat ulang. `testing/evals/dataset-stale.json` mengikat status ini pada checksum dataset lama. Angka potong manual merupakan metode berbeda; tidak dipakai sebagai jawaban acuan Kiss Cut.

Audit ukuran tanpa API jawaban/judge:

```bash
venv/bin/python -m testing.compare_chunking
```

Untuk membuat versi Pinecone eksperimen terpisah dan menjalankan benchmark retrieval k=3:

```bash
venv/bin/python -m testing.compare_chunking --index --output testing/comparisons/chunking-retrieval.json
```

Setiap pemanggilan dengan `--index` membuat draft eksperimen baru; tidak memublikasikannya. Semua kandidat memakai preprocessing section yang sama. Kandidat di atas batas token dilaporkan blocked; snapshot historis 1.500/200 tetap tersedia sebagai pembanding terpisah. Perbandingan baseline lama dengan kandidat baru juga mencakup perubahan preprocessing, bukan ukuran chunk saja.

Setelah review QA, pilih **Reviewed QA references** dan versi **1.000/100** di dashboard untuk menjalankan metrik jawaban. CLI yang sama dapat dipakai dengan versi tertentu:

```bash
RUN_PAID_EVALS=1 EVAL_DATASET=audited EVAL_KNOWLEDGE_VERSION=<version-id> EVAL_CASE_LIMIT=10 venv/bin/deepeval test run testing/evals/test_chatbot.py --identifier chunking-1000-100
```

Ganti `<version-id>` dengan ID versi ready. Bandingkan semua versi memakai referensi, model, judge, prompt dan top-k yang sama. Biaya API model berlaku untuk evaluasi jawaban; skor retrieval sumber-file yang tinggi belum membuktikan jawaban harga benar.

Pengujian boundary tanpa panggilan model:

```bash
LANGSMITH_TRACING=false venv/bin/python -m pytest testing/test_admin_workflow.py -q
```

DeepEval smoke test dengan API model:

```bash
RUN_PAID_EVALS=1 EVAL_CASE_LIMIT=1 venv/bin/deepeval test run testing/evals/test_chatbot.py --identifier smoke
```

Hilangkan `EVAL_CASE_LIMIT=1` untuk 10 pertanyaan asli. Skor di bawah threshold membuat quality test gagal; alasan dan skor tetap tersedia untuk diperiksa. Eval memakai API berbayar, dibatasi jumlah kasus/concurrency, dan tidak menjalankan loop optimasi otomatis.

40 kandidat skenario percakapan dibuat dengan `deepeval generate` dari konteks knowledge di `testing/evals/.dataset.json`. Periksa skenario, satuan, harga, dan expected outcome, edit JSON bila perlu, lalu tandai reviewed di dashboard. Setiap perubahan isi membatalkan status review. Sebanyak 32 kasus tersedia untuk development dan 8 dicadangkan sebagai held-out; gunakan held-out untuk penilaian akhir setelah menentukan konfigurasi.

Untuk suite percakapan setelah review:

```bash
RUN_PAID_EVALS=1 EVAL_DATASET=conversations EVAL_CASE_LIMIT=3 venv/bin/deepeval test run testing/evals/test_chatbot.py
```

Metrik QA: Faithfulness, Answer Relevancy, business correctness. Percakapan: Turn Faithfulness, Turn Relevancy, Conversation Completeness, business correctness. Threshold awal **0.7** adalah batas diagnostik. Kesalahan provider/metric dicatat terpisah dari nilai kualitas. Confident AI tidak dikonfigurasi; reporting memakai LangSmith.

Chroma sudah dipisahkan dari dependency runtime. Untuk reproduksi benchmark historis, gunakan environment Python 3.12 terpisah dengan `testing/requirements-baseline.txt`, lalu `VECTOR_STORE=chroma` dan koleksi Chroma lama atau koleksi yang dipulihkan dari snapshot. Jangan memasang dependency Chroma lama dan DeepEval baru pada environment runtime yang sama: keduanya membutuhkan versi PostHog yang berbeda.

## WhatsApp

Backend menerima webhook GET/POST di `/chat/whatsapp`. Untuk menerima pesan dari Fonnte, device WhatsApp perlu terhubung di Fonnte dan URL webhook harus dapat dijangkau melalui HTTPS. Untuk percobaan lokal, jalankan tunnel ngrok terpisah dan pasang `<URL-tunnel>/chat/whatsapp` pada konfigurasi webhook Fonnte.

Dashboard/playground dapat digunakan tanpa mengirim pesan WhatsApp. Pengujian dashboard tidak mengirim pesan ke pelanggan. Server lokal ini bukan konfigurasi deployment publik; frontend Vercel dan backend container tetap menjadi tahap deployment berikutnya.

## Struktur aktif

| Lokasi | Tanggung jawab |
| --- | --- |
| `app/main.py`, `app/routes.py` | Server, API chat, webhook WhatsApp |
| `app/admin/` | Auth, knowledge versions, PostgreSQL, job runner dan admin API |
| `app/backend/` | Loader, embedding/LLM, Pinecone, prompt dan RAG |
| `frontend/` | React + Vite + shadcn dashboard |
| `testing/evals/` | Dataset, metrik DeepEval, suite dan LangSmith bridge |
| `testing/baselines/`, `testing/comparisons/` | Capture historis dan perbandingan retrieval |
| `data/` | Data runtime lokal yang diabaikan Git |
| `docs/adr/`, `GLOSSARY.md` | Keputusan dan istilah proyek |


## Penyimpanan administrasi dan maintenance

Delapan tabel administrasi memakai schema privat `chatbot` pada Supabase PostgreSQL. Akses hanya melalui backend; frontend tetap memakai sesi dan CSRF API yang sama. Mode bersama `closed` → `intake` → `live` melindungi pemindahan data. Tidak ada fallback SQLite atau bootstrap knowledge saat startup.

Ikuti [runbook migrasi, verifikasi, dan batas rollback](docs/runbooks/supabase-state-cutover.md). SQLite lama dan backup dipertahankan sebagai arsip; file knowledge/evaluasi masih lokal. Migrasi database ini belum menyelesaikan kebutuhan deployment Vercel untuk worker, artefak, dan embedding.
