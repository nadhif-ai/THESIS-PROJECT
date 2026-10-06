# KERANGKA BERPIKIR ASLI — Narasi Dif
> Dipulihkan dari git history (commit: 36a602a1) pada 1 Oktober 2026.
> Ini adalah tulisan asli Dif sebelum progress.md distrukturisasi ulang.
> JANGAN DIEDIT — ini arsip referensi untuk penulisan naskah.

---

## Yang Belum Dilakukan

- Memahami observasi riwayat chat dari database WhatsApp
- Wawancara dengan Mas Aji (supervisor Asia Visual) pertama untuk mencari masalah apa? Wawancara kedua akhir-akhir ini dengan admin online untuk validasi bukti hasil observasi. Jadi: wawancara 1 → observasi → wawancara 2
- Meminta kuesioner human evaluation (validitas jawaban chatbot kepada orang Asia langsung: 2 deskprint dan 1 admin online — Mba Intan, Rizky, dan Shinta (admin))
- Meminta kuesioner untuk SUS/UAT kepada teman, rekan kerja selain human evaluation serta pelanggan Asia yang dikenal minimal 10–15 orang tentang fungsi chatbot. SUS dan UAT ini merangkap pengujian testing fungsionalitas black box — dilakukan sendiri mencakup kemampuan jawab chatbot, tombol di halaman kelola data (CRUD)
- Melakukan pengujian akurasi retrieval dengan precision dan hit rate
- Melakukan pengujian benchmark pada model OpenAI GPT-4o-Mini dan dua model lain jika bisa dengan pertimbangan cost termurah untuk UMKM, bisa cari di OpenRouter, dengan menguji latency, token usage dan token cost
- Belum melakukan rancangan diagram di Bab 3

---

## Bab 1 — Susunan Latar Belakang

- Kenaikan tren usaha digital printing dibanding offset (bisa ini) atau yang sudah ada saja yaitu percetakan secara umum yang mempengaruhi sektor lain dan kenaikan produksi cetak tahun terbaru
- Migrasi dari pemesanan offline menuju ke online via percakapan chat
- Keunggulan WhatsApp yang hampir dipakai semua UMKM
- Mengenalkan Asia Visual (sumber dari wawancara dengan Mas Aji → mengenalkan profil Asia Visual)
- Meningkatnya jumlah pengguna online yang datang ke Asia daripada offline (bisa sertakan data fiktif → dari hasil wawancara dengan Rizky, dengan Rizky juga yang ditanyakan adalah informasi yang belum terpusat dan terotomatisasi 24/7 sehingga menjadi beban Rizky)
- Kebanyakan pelanggan bertanya pada beberapa aspek pertanyaan yang dibuktikan dengan observasi (data chat WhatsApp) → data yang digunakan adalah data percakapan WhatsApp tahun 2025 dan dibagi dengan beberapa kategori pertanyaan
- Memberikan solusi berupa chatbot WhatsApp karena bisa otomatis menjawab dan menjadi pusat informasi yang belum terpusat serta meningkatkan efisiensi menjawab pertanyaan yang sering repetitif pada pertanyaan yang sama
- Menjelaskan karakteristik pelanggan yang bertanya dengan variasi bahasa yang bermacam-macam (berdasarkan data chat WhatsApp → dan memberikan pengenalan chatbot konvensional)
- Menjelaskan kekurangan chatbot konvensional kata kunci (hardcode lewat dictionary) dan mengenalkan RAG
- Menjelaskan RAG dari penelitian lain pada sektor berbeda dan menonjolkan kelebihannya
- Menjelaskan RAG itu butuh LLM sebagai generator → transisi (tersedia OpenRouter dan ada LLM gratis)
- Keterbatasan LLM via API yang gratis (jelek dalam meringkas, menangkap informasi dan responnya yang jelek)
- Memberikan opsi 3 model LLM terbaik menurut OpenRouter dengan ketentuan cost paling kecil dari vendor berbeda-beda (dibuktikan dengan screenshot OpenRouter — apakah hipotesa data OpenRouter itu sama dengan pengujian aslinya)
- Kesimpulannya: apa yang akan dilakukan di skripsi
- Mengimplementasikan chatbot serta mengujinya menggunakan metrik pengujian Hit Rate dan Precision (Recall bisa ditambah sebagai pertimbangan) serta metrik Human Evaluation (toko) dan SUS (orang asing)
- Menentukan 3 model tersebut yang paling sesuai untuk case Asia Visual UMKM

---

## Bab 1 — Identifikasi Masalah

- Belum ada solusi untuk pemusatan informasi di Asia Visual — semuanya serba manual seperti informasi toko dan menghitung produk digital printing
- Belum ada otomatisasi dan virtual asisten menjawab pelanggan untuk meningkatkan efisiensi kinerja setter
- Chatbot kata kunci lemah terhadap bentuk pertanyaan pelanggan yang banyak karena sifatnya hardcoded kaku
- LLM gratis seringkali kurang bagus untuk kemampuan menjawab (kaku dan tidak pintar mengambil potongan konteks) sehingga dicarilah LLM low-cost di OpenRouter

---

## Bab 1 — Rumusan Masalah → Kesimpulan (harus sama jumlahnya)
> Hindari kata "bagaimana" → cari kata "seberapa/manakah"

- Seberapa efektif sistem menjawab pertanyaan pelanggan (retrieval berhasil mengambil top-K) — dibuktikan dengan Hit Rate, Precision, dan Human Evaluation (validitas jawaban chatbot benar) dan SUS/UAT pada subjek selain Human Evaluation. Bahwa chatbot menjawab dengan benar dan membantu pengguna dibuktikan dengan kuesioner. Jika bisa dibuktikan dengan sebelum ada chatbot dan setelah ada chatbot — perbedaan delay waktu menjawab dari manual setter dengan chatbot berapa? Pada case bertanya harga banner
- Seberapa bagus kinerja model LLM dari ketiga model yang paling murah di OpenRouter yang paling cocok, dihitung dari token usage, latency, dan token cost (atau ada metrik lain dari OpenRouter bisa didiskusikan) sehingga didapatkan yang paling irit dan paling cepat
- Seberapa bagus chatbot secara fungsional?

---

## Bab 6 — Kesimpulan
> Wajib sama jumlahnya dengan Rumusan Masalah

- Menjawab sejauh mana efektivitas sistem menjawab pertanyaan — apakah retrieval bisa terambil semua dengan skor yang bagus dan kesimpulan YA sistem berhasil menarik dokumen dengan baik (dibuktikan dengan persentase di mana range persentase diskalakan dulu untuk menentukan BAIK atau TIDAKNYA — wajib ada skalanya. Jika SUS/UAT pakai Likert maka Hit Rate dan Precision pakai skala pengukuran dari jurnal)
- Menjawab model mana yang secara kinerja memiliki efisiensi yang baik (tidak harus memilih yang mana) tapi memberikan pilihan: model A unggul di metrik ini, model B unggul di metrik lainnya, misal token usage tapi jelek di latency
- Menjawab dari sisi fungsi tombol baik WhatsApp dan halaman kelola data berfungsi semua

---

## Bab 6 — Saran

- Membuat sistem CRUD untuk knowledge base yang lebih modern seperti tambah produk lalu dimasukkan ke knowledge base menggunakan sistem yang praktis dan simpel — tidak perlu ketik di .txt
- Menebalkan sisi keamanan dari injek file knowledge base .txt karena projek banyak celah otentikasi
- Memperkaya informasi di dokumen atau membuat strategi retrieval yang baik agar angka total harga produk selalu konsisten, misal menggunakan GraphRAG
- Mampu menganalisa gambar dan memberikan rekomendasi atau menjelaskan itu bahan apa dari gambar
- Mampu menjawab pertanyaan dari bahasa asing selain Indonesia
- Pengelolaan knowledge base sudah by table sistematis jadi proses CRUD sudah termasuk gambar — bisa lebih canggih (Multimodal RAG)
- Mampu meningkatkan kemampuan retrieval yang tepat sesuai pertanyaan dan tidak ambigu/meleset

---

## Bab 5 — Hasil Pembahasan
> Contoh penulisan: lihat jurnal layanan pelanggan dan KampusMadu

- Tabel pengukuran Hit Rate dan Precision — jelaskan pakai analisa dari pengaruh awal sampai faktor lain
- Tabel kinerja 3 model pada metrik latency, token usage, dan token cost (dari OpenRouter) dan Human Evaluation — berarti wajib ada 1 tabel kinerja LLM dan tabel jawaban LLM dari pertimbangan pakar Human Evaluation
- Tabel fungsi semua chatbot berfungsi baik — dibuktikan dengan PASS

---

## Bab 2 — Landasan Teori

- Menginputkan tinjauan pustaka yang belum semua dan kurang literatur 4 lagi
- Menuliskan isi setiap teori — pengujian juga dimasukkan seperti Hit Rate, Precision, dan sejenisnya
- Setiap sub-bab wajib teori disebutkan dari rujukan asli paper terdahulu
- Wajib tuliskan manfaatnya di implementasi (misal: Ngrok di sini saya gunakan untuk tunneling, dst.)
- Memaparkan model LLM semuanya (bisa gunakan OpenRouter)

---

## Bab 3 — Metode Penelitian
> Tulis rencananya saja bukan menggambar diagram dan lainnya.
> BAB 3 WAJIB SINGKAT → Bab 4 itu eksekusi dari perencanaan di Bab 3.
> Bab 3 jangan teknis.

### Metode Pengumpulan Data

**Timeline alur pengumpulan data:**
1. Saya (deskprint) menemukan masalah: belum terpusatnya informasi dan belum adanya otomatisasi → mengapa ini penting? Karena pekerjaan setter jadi lambat tanpa chatbot
2. Studi dokumentasi / observasi: membongkar database chat WhatsApp (mgstore.dbcrypt) dan melihat sekitar 300rb pesan tapi banyak noise
3. Wawancara pertama dengan Mas Aji (Juni/Juli 2026) — untuk mengenalkan profil perusahaan saja
4. Pembongkaran data di mgstore.dbcrypt dan melihat kategori pertanyaan
5. Wawancara kedua dengan Rizky — berkaitan dengan masalah yang dialami setter (belum terpusatnya informasi dan kendala molornya saat membalas)

**Kesimpulan urutan:**
> Wawancara Mas Aji → Observasi data chat (Studi Dokumentasi mgstore.dbcrypt) → Wawancara Rizky → Studi Literatur → Studi Dokumentasi lagi (katalog harga) → pertanyaan di mgstore.dbcrypt jadi referensi membangun knowledge base dengan kurasi ke file .txt → Implementasi chatbot

**Catatan bingung Dif (perlu didiskusikan):**
- Data primer: masih bingung tujuannya apa — apakah wawancara dan observasi? Bukankah keduanya hanya sebagai validasi membangun masalah?
- Data sekunder: membaca literatur terkait (studi literatur), studi dokumentasi → mgstore.dbcrypt (kumpulan riwayat percakapan pelanggan Asia 2025) & katalog harga produk Asia 2026
- Bingung membedakan "studi dokumentasi" vs "observasi" saat membongkar mgstore.dbcrypt

### Metode Pengembangan Sistem (Prototyping)

**Tahap Komunikasi:**
- Mengumpulkan data knowledge base → dari chat WA Asia 2025 dan katalog Asia 2026
- Mengumpulkan kebutuhan fungsional → fungsi/fitur apa saja yang HARUS BISA dilakukan → dibuat tabel nanti di Bab 4
- Mengumpulkan kebutuhan sistem → software, hardware, platform (wajib sertakan versi) → dibuat tabel nanti di Bab 4

**Tahap Perencanaan Cepat:**
- Menyebutkan dengan gamblang bahwa membangun data secara manual → kurasi dari data katalog menjadi file .txt, membuka mgstore.dbcrypt, mengklasifikasikan pertanyaan yang cocok dan menjadikannya referensi dengan membaginya menjadi kategori: SOP toko, penjelasan bahan dan finishing dalam bentuk .txt
- Menyebutkan tipe RAG yang akan digunakan (Naive RAG) disertai alasannya, merencanakan metode chunking-nya apa dan berapa ukurannya
- Menyebutkan pengujian yang akan dilakukan disertai alasannya

**Tahap Pemodelan Cepat / Sistem:**
> SEMUANYA DIAGRAM dari UML dan Arsitektur RAG dan Arsitektur Chatbot secara utuh (FastAPI, Chroma, WhatsApp, Fonnte, LangChain)
- Membuat Use Case Diagram dan Activity Diagram antara petugas dan pengguna chatbot
- Membuat alur arsitektur RAG dan Arsitektur Chatbot
- Membuat alur pengujian akan bagaimana

**Tahap Konstruksi/Implementasi:**
- Pembuatan API routing WhatsApp ke sistem chatbot menggunakan Fonnte
- Implementasi RAG pada chatbot

**Pengujian & Push ke GitHub**

---

## Bab 4 — Implementasi
> Rancangan di Bab 3 dieksekusi di Bab 4.
> Bab 3 hanya rencana tanpa isi implementasi sama sekali.
> Bab 3 jangan teknis — Bab 4 isinya koding dan tutorial langkah-langkah.

- Cara konfigurasi Fonnte ke RAG → gambar Fonnte
- Cara merancang API di routes.py sehingga data bisa mengalir → gambar list endpoint
- Cara membuat knowledge base (kurasi dari katalog harga dan sintetis manual) — diawali dengan mengumpulkan (augmentasi knowledge base) dan cara mengelola di halaman kelola data → gambar screenshot file .txt semuanya
- Cara melihat struktur dalam dari ChromaDB untuk pembuktian bahwa kita bisa melihat dari angka-angka vektor → gambar ChromaDB menggunakan DBeaver (mungkin) untuk akses isi SQLite di ChromaDB
- Cara membuat sistem RAG dari konfigurasi chunk, RecursiveTextSplitter, proses dari .txt ke vektor — dari indexing, ingestion, embedding dengan model LLM OpenRouter, Top-K, chunk, retrieval, prompt template, generation
- Cara menguji akurasi RAG dengan Hit Rate dan Precision → memberikan kuesioner baik SUS, UAT, dan Human Evaluation dengan penjelasan skalanya dari range berapa ke berapa

---

## Catatan Dosen Penguji

- Bu Viva: ada di hari Selasa sejam doang dari jam 8–9, sisanya zoom
- Bu Faiz: kalau revisi mintanya pakai notulensi, apa yang dikerjakan dilabelin kuning
