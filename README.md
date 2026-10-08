# Chatbot Informasi CV. Asia Visual Grafika (RAG + WhatsApp)

Chatbot WhatsApp untuk usaha percetakan digital **CV. Asia Visual Grafika**. Chatbot menjawab pertanyaan pelanggan tentang **bahan, harga, ketentuan berkas desain, dan SOP toko** berdasarkan dokumen milik toko, bukan dari "ingatan" AI. Teknik ini disebut **RAG** (*Retrieval-Augmented Generation*).

Chatbot hanya memberi **informasi**. Ia tidak memproses pesanan atau pembayaran; itu tetap dilakukan admin toko.

Repositori: https://github.com/nadhif-ai/THESIS-PROJECT

---

## 1. Cara kerja singkat

1. Pelanggan mengirim pesan ke WhatsApp toko. Layanan **Fonnte** meneruskannya ke server lewat *webhook*.
2. Server (**FastAPI**) memeriksa pesan. Sapaan, perintah *reset*, dan menu angka 1-4 dijawab langsung tanpa AI.
3. Pertanyaan lain dicari di basis pengetahuan (**ChromaDB**, 10 potongan dokumen paling mirip), lalu dirangkai bersama riwayat chat menjadi *prompt*.
4. **LLM** (Gemini lewat OpenRouter) menyusun jawaban dari potongan dokumen itu. Jawaban dikirim balik lewat Fonnte.

## 2. Komponen

| Komponen | Fungsi |
|---|---|
| FastAPI + Uvicorn | Server: *webhook* WhatsApp dan portal admin |
| LangChain | Merangkai pencarian, *prompt*, dan LLM |
| ChromaDB | Penyimpanan vektor (folder `chroma_db`, dibuat otomatis) |
| `intfloat/multilingual-e5-small` | Model *embedding* lokal (teks menjadi vektor) |
| OpenRouter (default `google/gemini-2.5-flash`) | Akses ke LLM |
| Fonnte | Penghubung WhatsApp (terima dan kirim pesan) |
| ngrok | Membuka server lokal ke internet agar bisa dipanggil Fonnte |
| Portal admin `/admin` | Lihat riwayat chat dan kelola berkas pengetahuan |

## 3. Struktur folder

| Lokasi | Isi |
|---|---|
| `app/main.py` | Titik masuk aplikasi |
| `app/routes.py` | *Endpoint*: *webhook* WhatsApp dan portal admin |
| `app/dependencies.py` | Membangun ulang indeks dan memantau perubahan KB |
| `app/backend/` | `loader.py` (baca dan potong dokumen), `vectorstore.py` (ChromaDB), `models.py` (embedding dan LLM), `prompt_template.py` (aturan jawaban), `chain.py` (alur RAG) |
| `app/config/settings.py` | Pembaca pengaturan dari `.env` |
| `app/frontend/admin.html` | Halaman portal admin |
| `dataset/knowledge_base/` | 6 berkas pengetahuan toko (`01_` sampai `06_`, `.txt`) |
| `dataset/admin_chat_history.json` | Riwayat chat yang tersimpan |
| `testing/` | Skrip dan soal uji *retrieval* |
| `run-app.bat` | Menjalankan FastAPI dan ngrok sekaligus |

---

## 4. Instalasi (Windows)

### Yang perlu disiapkan

- Windows 64-bit, **Python 3.10**, dan **Git**.
- Akun **OpenRouter** (butuh API key).
- Akun **Fonnte** dengan satu perangkat WhatsApp yang sudah terhubung (butuh token).
- Akun **ngrok** (butuh *authtoken*; domain statis opsional).
- Koneksi internet untuk instalasi pertama (paket Python berukuran beberapa GB karena `torch`).

### Langkah

**1. Unduh proyek**

```bat
git clone https://github.com/nadhif-ai/THESIS-PROJECT.git
cd THESIS-PROJECT
```

**2. Buat lingkungan Python bernama `venv`** (nama ini wajib, karena dipakai `run-app.bat`)

```bat
py -3.10 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
```

**3. Pasang dependensi**

```bat
pip install -r requirements.txt
pip install watchdog
```

`watchdog` belum tercantum di `requirements.txt`, tetapi dibutuhkan agar indeks otomatis diperbarui saat berkas pengetahuan berubah. `python-telegram-bot` di `requirements.txt` tidak dipakai kode.

**4. Unduh model *embedding* satu kali**

Aplikasi berjalan dalam mode *offline* untuk HuggingFace, jadi model harus sudah ada di komputer. Jalankan di terminal biasa (bukan lewat `run-app.bat`):

```bat
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-small')"
```

**5. Buat berkas `.env`** di folder utama (sejajar dengan `run-app.bat`). Berkas ini tidak ada di repositori dan tidak boleh di-*commit*.

```env
OPENROUTER_API_KEY=isi_api_key_openrouter
OPENROUTER_MODEL=google/gemini-2.5-flash
FONNTE_TOKEN=isi_token_fonnte
NGROK_DOMAIN=nama-domain-anda.ngrok-free.app
```

| Variabel | Wajib | Keterangan |
|---|---|---|
| `OPENROUTER_API_KEY` | Ya | Tanpa ini aplikasi gagal menyala |
| `FONNTE_TOKEN` | Ya, untuk WhatsApp | Tanpa ini balasan tidak terkirim |
| `OPENROUTER_MODEL` | Tidak | Bawaan `google/gemini-2.5-flash`; samakan dengan model yang dipakai saat pengujian skripsi |
| `NGROK_DOMAIN` | Tidak | Tulis tanpa `https://`. Jika kosong, ngrok memakai alamat acak yang berubah setiap dijalankan |
| `EMBEDDING_MODEL`, `SEMANTIC_TOP_K`, `CHROMA_PERSIST_DIR`, `LOG_LEVEL` | Tidak | Bawaan: `intfloat/multilingual-e5-small`, `10`, `./chroma_db`, `INFO` |

**6. Daftarkan *authtoken* ngrok** (cukup sekali; `ngrok.exe` sudah ada di folder proyek)

```bat
ngrok.exe config add-authtoken ISI_AUTHTOKEN_NGROK
```

**7. Jalankan**

Klik dua kali `run-app.bat`. Dua jendela terbuka: **FastAPI** dan **ngrok**. Pada jalan pertama, indeks ChromaDB dibangun otomatis sehingga startup lebih lama. Tunggu sampai jendela FastAPI menampilkan "RAG system initialized successfully".

**8. Hubungkan WhatsApp**

Di dashboard Fonnte, buka pengaturan perangkat dan isi *Webhook URL*:

```
https://NAMA-DOMAIN-NGROK/chat/whatsapp
```

Kirim pesan ke nomor WhatsApp toko untuk mencoba.

---

## 5. Memeriksa bahwa sistem berjalan

| Alamat | Fungsi |
|---|---|
| http://localhost:8000/docs | Dokumentasi API; bisa mencoba `POST /chat/faq` tanpa WhatsApp (isi `session_id` dan `question`) |
| http://localhost:8000/admin | Portal admin (login; kredensial ada di bagian login `app/routes.py`) |

## 6. Masalah yang sering terjadi

| Gejala | Penyebab dan solusi |
|---|---|
| Error `OPENROUTER_API_KEY` *field required* | `.env` belum dibuat atau salah letak |
| Gagal memuat model saat startup | Langkah 4 belum dilakukan |
| Pesan WhatsApp tidak dibalas | Periksa *webhook* di Fonnte, `FONNTE_TOKEN`, status perangkat Fonnte, dan jendela ngrok masih terbuka |
| Alamat ngrok berubah dan bot berhenti membalas | `NGROK_DOMAIN` kosong; isi domain statis atau perbarui *webhook* di Fonnte |
| Isi KB diubah tapi jawaban lama | `watchdog` belum terpasang; pasang lalu restart |
| Ingin mengosongkan indeks | Hentikan aplikasi, hapus folder `chroma_db`, jalankan ulang |

---

## 7. Catatan untuk penulis Bab IV

**Urutan membaca kode** (dari alur paling dasar):
`main.py` → `dependencies.py` → `loader.py` → `vectorstore.py` → `models.py` → `prompt_template.py` → `chain.py` → `routes.py` (bagian *webhook* dan `/admin`).

**Pengujian *retrieval*** ada di `testing/run_evaluation.py` (Hit Rate@3 dan Precision@3 atas soal di `test_dataset.csv`). Jalankan setelah ChromaDB terisi: `python testing/run_evaluation.py`.

**Bagian kode yang tidak dipakai** alur WhatsApp maupun portal admin. Tidak perlu didokumentasikan:

- `routes.py`: *endpoint* `/chat/questions`, `/chat/question/{id}`, `/price-calculator`, `/api/calculator/data`, dan `/chat/media/gdrive/...` (berkas pendukungnya tidak ada di repositori).
- `main.py`: rute `/` (berkas `index.html` tidak ada).
- `chain.py`: parameter `intent_filter`, penanganan `media_url`, dan fungsi `clear_all_session_histories`.
- `temp_script_0.js`: salinan lama skrip portal admin.
- `python-telegram-bot`: sisa fase awal.

Yang aktif: *webhook* `/chat/whatsapp`, delapan *endpoint* `/admin/api/*`, serta `/chat/faq` dan `/chat/reset` sebagai jalur uji lewat REST.
