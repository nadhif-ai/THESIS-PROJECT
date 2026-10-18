# Chatbot Asia Visual Grafika — RAG + WhatsApp

Chatbot informasi percetakan untuk satu bisnis. Pelanggan menggunakan WhatsApp melalui WAHA; administrator mengelola dokumen, menguji jawaban, mengatur model, dan melihat evaluasi di dashboard React + shadcn. Integrasi Fonnte tersedia untuk rollback.

Pipeline yang sama dipakai WhatsApp, playground, dan evaluasi: embedding Nemotron melalui OpenRouter → pencarian Pinecone → jawaban OpenRouter. LangSmith menyimpan trace dan hasil eksperimen; DeepEval menghitung metrik kualitas. Chatbot memberikan informasi; pemesanan dan pembayaran tetap ditangani admin toko.

## Menjalankan di macOS

Gunakan Python **3.12** dan Node **22.12+**. Jalankan perintah dari root proyek:

```bash
uv venv --python 3.12 venv
uv pip install --python venv/bin/python -r requirements.txt
```

Untuk membuat environment baru, salin `.env.example` menjadi `.env` lalu isi kredensial. Jika `.env` sudah ada, gunakan file tersebut.

Embedding memakai API OpenRouter; tidak perlu mengunduh model lokal:

```bash
venv/bin/python -c "from app.backend.models import get_embedding_model; assert len(get_embedding_model().embed_query('uji koneksi')) == 2048; print('Embedding ready: 2048 dimensions')"
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

Buka [halaman utama](http://127.0.0.1:8000/), [login administrator](http://127.0.0.1:8000/admin/login), [dashboard admin](http://127.0.0.1:8000/admin/), atau [API docs](http://127.0.0.1:8000/docs). Halaman utama bersifat publik; data workspace tetap memerlukan sesi administrator. State administrasi harus dimigrasikan terlebih dahulu mengikuti [runbook Supabase](docs/runbooks/supabase-state-cutover.md). Akun, hash password, dan sesi lama dipertahankan; startup tidak membuat akun atau mengimpor data secara otomatis. Kredensial lama tetap berlaku.

Untuk development frontend, jalankan `npm run dev` dari `frontend/` di terminal kedua dan buka [Vite halaman utama](http://127.0.0.1:5173/) atau [Vite admin](http://127.0.0.1:5173/admin/). Permintaan admin API diteruskan ke backend port 8000.

## Konfigurasi

| Variabel | Keterangan |
| --- | --- |
| `PINECONE_API_KEY`, `PINECONE_INDEX_NAME` | Indeks `chatbot-nadhif`, vector dense **2048 dimensi, cosine** |
| `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` | Provider dan model pemberi jawaban |
| `EVAL_MODEL` | Model judge terpisah; default `google/gemini-2.5-flash` |
| `SEMANTIC_TOP_K` | Jumlah passage untuk jawaban; dapat diubah di Providers |
| `LANGSMITH_TRACING`, `LANGSMITH_ENDPOINT`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` | Trace dan laporan evaluasi |
| `LANGSMITH_WORKSPACE_ID` | Opsional jika key LangSmith memerlukan workspace organisasi |
| `WHATSAPP_PROVIDER` | `waha` untuk koneksi aktif, atau `fonnte` untuk integrasi lama |
| `WAHA_BASE_URL`, `WAHA_API_KEY`, `WAHA_SESSION` | Server WAHA, API key, dan nama session yang sudah terhubung |
| `WAHA_WEBHOOK_SECRET`, `WAHA_WEBHOOK_URL` | Secret HMAC dan alamat callback HTTPS backend |
| `FONNTE_TOKEN` | Token integrasi lama; hanya digunakan ketika provider `fonnte` |
| `DATABASE_URL` | Koneksi PostgreSQL runtime dengan role terbatas `chatbot_app` |
| `DATABASE_MIGRATION_URL` | Koneksi operator untuk migrasi eksplisit; tidak dipakai runtime |
| `DATA_DIR` | Berkas knowledge, artefak evaluasi, dan backup lokal; default `./data` |
| `COOKIE_SECURE`, `ALLOWED_ORIGINS` | Cookie dan origin untuk lingkungan HTTPS atau origin tambahan |

Kunci tidak dikirim ke browser. Pengaturan model dan retrieval disimpan di PostgreSQL; nilai dashboard yang telah disimpan memiliki prioritas terhadap default `.env`. Runtime aktif memakai `nvidia/nemotron-3-embed-1b:free` melalui OpenRouter dengan `EMBEDDING_DIMENSIONS=2048`. Versi menyimpan identitas embedding dan index; versi E5 lama hanya menjadi arsip. Pergantian embedding memerlukan reindex. Prosedur persiapan, evaluasi, dan peralihan WhatsApp tersedia di [runbook migrasi Nemotron](docs/runbooks/nemotron-embedding-migration.md).

## Menggunakan dashboard

1. **Dashboard**: status knowledge, aktivitas, waktu respons, dan baseline retrieval.
2. **Knowledge**: satu daftar sumber TXT/PDF teks. Upload langsung ke private Supabase Storage; preview file asli, teks dan passage. TXT dapat diedit; PDF diganti lewat **Replace**. Switch aktif/nonaktif dan hapus per sumber baru berlaku setelah **Sync knowledge**. Batas per file 10 MB, PDF 300 halaman, hasil ekstraksi 1 MB UTF-8; PDF scan memerlukan OCR sebelum upload.
   Di **Passage configuration**, simpan ukuran karakter dan overlap. Migrasi awal mempertahankan konfigurasi aktif 1.500/200 dengan preprocessing legacy; instalasi kosong dimulai 1.000/100. Menyimpan konfigurasi baru memakai pemisahan section dengan heading pada passage. Nilai karakter berbeda dari token. Embedding tetap Nemotron/OpenRouter 2.048 dimensi di `chatbot-nadhif`.
3. **Playground**: knowledge tersinkron terbaru, tanpa pemilih versi; lihat konteks/sumber, penggunaan token, dan trace LangSmith. Sesi playground terpisah dari pelanggan.
4. **Sync knowledge** membangun namespace pengganti, memverifikasi vector, lalu mengaktifkannya secara atomik. Editing Knowledge terkunci selama sinkronisasi; data sebelumnya tetap melayani hingga penggantinya siap. Jika semua sumber nonaktif/dihapus, bot menjawab “Maaf Kak, informasi tersebut belum tersedia saat ini.” Evaluasi baru memerlukan knowledge yang dapat dicari.
5. **Conversations**: filter WhatsApp, playground, API, atau evaluasi. Riwayat lama diimpor sekali tanpa mengubah file asal.
6. **Providers**: model jawaban, model judge, top-k, dan status konfigurasi kredensial.
7. **Evaluations**: jalankan pertanyaan asli atau skenario percakapan yang telah direview; periksa skor/alasan per kasus, ekspor JSON, dan buka eksperimen LangSmith.

Sinkronisasi dan evaluasi memakai checkpoint PostgreSQL, lease eksekusi dan Vercel Queues; lokal menjalankan state machine yang sama. Evaluasi menangkap knowledge, dataset dan konfigurasi model saat Mulai, konsisten walaupun sync lain selesai. **Resume** meneruskan checkpoint setelah kegagalan; panggilan provider yang terputus sebelum checkpoint mungkin terulang. File/vector lama dibersihkan setelah grace 24 jam dan tidak dipin konfigurasi/pekerjaan yang masih memerlukannya. [Kontrak dan prosedur migrasi KB global](docs/single-knowledge-base.md).

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

Setelah review QA, pilih **Reviewed QA references** di dashboard. Run baru selalu memakai knowledge tersinkron terbaru. CLI juga menangkap knowledge aktif dan konfigurasi saat suite dimulai:

```bash
RUN_PAID_EVALS=1 EVAL_DATASET=audited EVAL_CASE_LIMIT=10 venv/bin/deepeval test run testing/evals/test_chatbot.py --identifier current-knowledge
```

Variabel `EVAL_KNOWLEDGE_VERSION` sudah dihentikan. Bandingkan hasil historis memakai referensi, model, judge, prompt dan top-k yang dicatat. Biaya API model berlaku; skor retrieval sumber-file yang tinggi belum membuktikan jawaban harga benar. Eksperimen chunking CLI di atas adalah tooling reproduksi terpisah, bukan konfigurasi KB pada dashboard.

Pengujian boundary tanpa panggilan model:

Tes administrasi memerlukan PostgreSQL disposable pada loopback port 54585; fixture tidak memakai Supabase production. Lihat [persiapan database tes](docs/runbooks/supabase-state-cutover.md#verification-and-deployment-boundary).

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

Production memakai webhook `https://chatbotta-nadhif.vercel.app/chat/waha/webhook` dan consumer Vercel Queues. WAHA tetap berjalan terpisah di laptop Linux. Mac tidak diperlukan untuk pemrosesan production.

### Pengembangan lokal (opsional)

Koneksi saat ini menggunakan session `asia-chatbot` pada WAHA GOWS. Mac dan VPS berada di jaringan Tailscale yang sama. Jalankan backend di Mac:

```bash
venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Aktifkan callback HTTPS privat melalui Tailscale Serve (konfigurasinya persisten):

```bash
tailscale serve --bg --https=8443 http://127.0.0.1:8000
tailscale serve status
```

Callback yang terpasang pada session WAHA:
`https://royans-macbook-pro.tail14234e.ts.net:8443/chat/waha/webhook`.
Jika pindah host, sesuaikan hostname pada `WAHA_WEBHOOK_URL` dan konfigurasi webhook WAHA.

Di konfigurasi session WAHA, gunakan event **`message`** dan **`message.ack`**, HMAC key yang sama dengan `WAHA_WEBHOOK_SECRET`, serta retry constant dengan delay 2 detik dan 5 attempts. Jangan membagikan API key atau secret. Session harus berstatus **WORKING**. Dashboard **Providers** menampilkan status session, worker, dan antrean; tombol Refresh memperbarui status.

Webhook memverifikasi HMAC SHA-512 atas body asli, menyimpan pesan ke antrean PostgreSQL, lalu worker menjalankan pipeline RAG dan mengirim balasan. Pesan berulang dengan ID sama tidak diproses ulang. Pesan dari akun bot sendiri, grup, serta pesan tanpa teks diabaikan. Gunakan satu proses Uvicorn untuk antrean ini. Pengiriman yang terputus atau tidak pasti ditandai `uncertain`; periksa WhatsApp sebelum mencoba mengirim ulang.

Mac harus tetap menyala dengan backend dan Tailscale aktif. WAHA di VPS saja belum cukup untuk menjawab pesan ketika Mac tidur atau backend berhenti. Untuk operasi terus-menerus, pindahkan backend dan data persisten ke host yang selalu aktif.

### Preview gambar

Pipeline mengirim gambar ketika dokumen hasil retrieval memiliki metadata `media_url`. Tambahkan penanda `[MEDIA: https://host/gambar.png]` pada sumber, lalu **Sync knowledge** dan periksa Playground. Pipeline memilih URL pertama dari hasil retrieval. Mengunggah PDF tidak otomatis menghasilkan foto produk untuk WhatsApp.

Gunakan URL HTTPS gambar PNG/JPEG yang dapat diunduh dari server WAHA. URL localhost akan diterjemahkan ke host HTTPS callback yang dikonfigurasi. Gambar dikirim melalui `/api/sendImage`, lalu jawaban lengkap melalui `/api/sendText`. Jika gambar gagal, balasan teks tetap dicoba. Verifikasi koneksi awal berhasil mengirim teks dan PNG diagnostik kepada pengirim pesan uji; keduanya menerima delivery acknowledgement `2`.

### Rollback Fonnte

Set `WHATSAPP_PROVIDER=fonnte`, pastikan `FONNTE_TOKEN` tersedia, restart backend, dan arahkan webhook Fonnte ke URL HTTPS `/chat/whatsapp`. Ketika provider `waha`, endpoint Fonnte mengabaikan pesan agar tidak ada dua integrasi yang membalas bersamaan. Backup konfigurasi session WAHA sebelum migrasi disimpan lokal di `data/waha/`; file tersebut berisi konfigurasi privat dan tidak boleh dibagikan.

Dashboard/playground dapat digunakan tanpa mengirim pesan WhatsApp. Pengujian dashboard tidak mengirim pesan ke pelanggan. Server lokal ini bukan konfigurasi deployment publik; deployment Vercel tetap memerlukan tahap worker persisten, penyimpanan artefak, dan konfigurasi routing.

## Struktur aktif

| Lokasi | Tanggung jawab |
| --- | --- |
| `app/main.py`, `app/routes.py` | Server, API chat, webhook WhatsApp |
| `app/integrations/waha.py` | Webhook WAHA, antrean persisten, pengiriman teks/gambar dan receipts |
| `app/admin/` | Auth, KB global, private originals, PostgreSQL, checkpoint jobs dan admin API |
| `app/backend/` | Loader, embedding/LLM, Pinecone, prompt dan RAG |
| `frontend/` | React + Vite + shadcn dashboard |
| `testing/evals/` | Dataset, metrik DeepEval, suite dan LangSmith bridge |
| `testing/baselines/`, `testing/comparisons/` | Capture historis dan perbandingan retrieval |
| `data/` | Data runtime lokal yang diabaikan Git |
| `docs/adr/`, `GLOSSARY.md` | Keputusan dan istilah proyek |


## Penyimpanan administrasi dan maintenance

Delapan tabel administrasi memakai schema privat `chatbot` pada Supabase PostgreSQL. Akses hanya melalui backend; frontend tetap memakai sesi dan CSRF API yang sama. Mode bersama `closed` → `intake` → `live` melindungi pemindahan data. Tidak ada fallback SQLite atau bootstrap knowledge saat startup.

Ikuti [runbook migrasi, verifikasi, dan batas rollback](docs/runbooks/supabase-state-cutover.md). SQLite lama dan backup dipertahankan sebagai arsip; file knowledge/evaluasi masih lokal. Migrasi database ini belum menyelesaikan kebutuhan deployment Vercel untuk worker, artefak, dan embedding.

## Performa dashboard

Jika mengubah `.env` (termasuk `PINECONE_INDEX_NAME`), restart backend: konfigurasi dan klien provider disimpan selama proses berjalan. Startup memvalidasi bahwa index Pinecone sesuai dengan Nemotron (2048 dimensi, cosine); mengubah nama index tidak memindahkan namespace atau embedding. Jalur chat hanya membaca metadata versi knowledge, bukan snapshot embedding. Lihat [perbaikan Playground dan WhatsApp](testing/rag-whatsapp-recovery-20261016.md).

Read API memeriksa session dan membaca snapshot dalam satu perintah PostgreSQL melalui simple query protocol yang kompatibel dengan transaction pooler. `Server-Timing` di DevTools memisahkan waktu akuisisi koneksi, pembacaan database, dan request aplikasi. Login melaporkan fase database, verifikasi password, dan pembuatan session. Request admin yang melebihi satu detik mencatat statistik pool tanpa credential atau isi percakapan.

Jika gangguan jaringan menghabiskan periode reconnect, callback pool memulai pemulihan koneksi lagi. Ini mencegah pool kosong macet ketika antrean request yang sudah timeout memenuhi batas antrean. Gangguan database tetap mengembalikan 503 sampai koneksi pulih; operasi tulis dan pengiriman WhatsApp tidak diulang oleh mekanisme ini.

Koneksi yang kehilangan balasan dibatasi I/O 35 detik dan transaksi idle dibatasi 35 detik. Akuisisi koneksi dan siklus reconnect memakai anggaran 15 detik. Session awal mencoba ulang gangguan sementara secara otomatis; read biasa dibatasi dua percobaan tambahan. GET/HEAD memiliki deadline browser 20 detik. Status 401/403 tetap mengakhiri sesi sesuai respons backend. Lihat [investigasi 503 berulang dan bukti pemulihan](testing/dashboard-resilience-fix.md).

TanStack Query menyimpan cache dalam memori tab, melakukan prefetch satu tujuan saat sidebar di-hover/fokus, dan menampilkan widget evaluasi secara independen. Cache privat dibersihkan saat logout/session berakhir. Respons admin memakai `Cache-Control: private, no-store`.

Versi baru menyimpan jumlah chunk dalam metadata. Untuk data lama, jalankan backfill idempoten dari root repository dengan runtime role `chatbot_app` dan mode `live`:

```bash
venv/bin/python -m scripts.backfill_version_metadata
```

Lihat [hasil pengukuran dan batas target di bawah satu detik](testing/dashboard-subsecond-implementation.md). Waktu cold start, login production, dan penempatan backend dekat database tetap perlu diperiksa saat deployment.
