# Investigasi kualitas retrieval dan generasi — 28 Oktober 2026

Status: rancangan disetujui dan kode diimplementasikan di workspace; runtime baru belum dideploy. SOP sudah disinkronkan ke produksi. Pengguna menyetujui prioritas jawaban lengkap dengan satu langkah pemulihan otomatis yang dibatasi. Transkrip awal ada di [playground-result.md](playground-result.md); ekstrak trace dari pengujian tersebut ada di [playground-trace-evidence.json](playground-trace-evidence.json). Tidak ada percakapan pelanggan lain yang diekspor.

## Kesimpulan

Pernyataan bahwa data ada di dokumen benar. Ada empat kegagalan berbeda di jalur penggunaannya:

1. SOP ada dalam sumber staged, tetapi tidak masuk versi published yang dipakai pelanggan.
2. Data tujuh kertas dan tarif ada dalam versi published, tetapi pemilihan lima passage tidak mencakup fakta yang diperlukan pertanyaan gabungan.
3. Pada permintaan gambar, keputusan classifier mematikan retrieval meskipun jawaban diminta memuat detail produk.
4. Generasi teks kehabisan anggaran output dan hasil terpotong tetap dikirim sebagai jawaban.

Menambah prompt agar model membaca knowledge lebih teliti tidak menyelesaikan fakta yang tidak pernah masuk ke konteks model.

## Bukti dan akar masalah

### A. SOP tidak termasuk snapshot pelanggan

Pembacaan database secara read-only kembali memastikan versi published `kb-c771d8efa03c49c6949561488ce70f67` memiliki 128 passage dari lima file 02–06. SOP 01 tidak ada di manifest. Versi sebelumnya `kb-84668f0b823a402cbe360c2c711bd766`, disinkronkan 24 Oktober 2026 pukul 11.01 WIB, mencakup keenam file. Versi aktif disinkronkan 27 Oktober pukul 23.29 WIB; source SOP sekarang enabled dan diperbarui pukul 23.37 WIB. State sekarang revision 22, applied revision 21, tanpa sync yang berjalan.

`app/admin/kb_store.py:196` menangkap sumber enabled yang belum dihapus saat sync dimulai. `app/admin/global_knowledge.py:207` menyimpan daftar tersebut dalam manifest; aktivasi baru terjadi setelah proses verifikasi. Karena versi aktif memang tidak memuat SOP, embedding dan reranker tidak bisa mengembalikan jam buka atau nomor admin darinya.

Penyebab langsung terkonfirmasi: perbedaan sumber staged dan published. Belum ada bukti audit siapa atau tindakan apa yang mengeluarkan SOP saat revision 21; jangan menyebutnya bug penghapusan atau kegagalan Pinecone tanpa bukti tersebut. Kegagalan jam buka juga terjadi tanpa riwayat, seperti kasus 10 transkrip.

### B. Fakta aktif hilang di pemilihan konteks

[Trace retrieval kasus tujuh kertas](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/ac00eeb0-7d99-4513-92fe-9e366ae6b9e8/trace/01a181c8-d63d-7352-97b4-5c66f200f589/run/01a181c8-ddff-72f2-ad8f-9f80b303a8b3?start_time=2026-10-28T09:13:07.327894Z) memperlihatkan satu query untuk tiga kebutuhan: membandingkan tujuh bahan, merekomendasikan bahan sertifikat, dan memperkirakan biaya. Query juga memuat riwayat Roll Up Banner/Ciputat yang sudah tidak berkaitan dengan produk baru.

Database versi aktif memastikan spesifikasi tujuh bahan tersebar pada chunk 7–13 dari file 02. Tarif Linen untuk 11–50 lembar ada di chunk 23 dan duplikatnya 48 dari file 04. Jadi tarif yang relevan benar-benar tersedia dalam snapshot, bukan sekadar di file lokal.

| Tahap | Bukti trace | Dampak |
|---|---|---|
| Dense retrieval | 20 kandidat | Chunk 13 berisi karakteristik Photopaper tidak masuk kandidat; pencarian leksikal setelah tahap ini tidak bisa memulihkannya. |
| Kandidat | 20 chunk ID, tetapi hanya 17 teks unik | Pasangan 21/46, 23/48, 24/49 memuat teks identik; duplikasi mengurangi keragaman kandidat. |
| Reranking | Lima terpilih: file 02 chunk 12 dan 11; file 04 chunk 20, 18, 67 | Terfokus pada kecocokan sertifikat dan formula, bukan kelengkapan tujuh bahan dan tarif untuk jumlah pelanggan. |
| Tarif | Chunk 23/48 sudah ada dalam 20 kandidat, tetapi keduanya dibuang | Tarif Linen 20 lembar tidak diterima model. |
| Konteks model | System message knowledge hanya memuat lima teks terpilih | Model tidak menerima uraian lengkap HVS, Art Paper, Art Carton, BW dan Photopaper. Chunk 12 hanya berakhir pada judul Photopaper. |

Skor reranker lima hasil adalah 0,9035; 0,8844; 0,8834; 0,8347; 0,8299. Skor tinggi menunjukkan relevansi terhadap query, bukan kelengkapan jawaban gabungan. Nilai Similarity di UI adalah cosine similarity asli, bukan skor reranker.

Kode pemilik: `app/backend/vectorstore.py:106` mengambil dense candidates; `app/backend/retrieval_ranking.py:18` menghitung lexical rank hanya pada kandidat tersebut; `:88` memilih hasil reranker sampai k; `app/backend/chain.py:547` membuat satu query dan `:641` menyusun konteks. Tidak ada pemeriksaan cakupan per kebutuhan atau perluasan ke bagian terkait dari snapshot yang sama.

Chunking juga memisahkan nama bahan dari uraian/penggunaannya karena daftar bahan berupa nomor biasa, bukan subjudul Markdown. `app/admin/chunking.py:35` mempertahankan heading, lalu memecah isi menurut batas karakter. Ini menjelaskan kenapa passage tentang satu bahan dapat diawali lanjutan penggunaan bahan sebelumnya.

### C. Classifier mematikan retrieval pada gambar

[Intent perbandingan kertas](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/ac00eeb0-7d99-4513-92fe-9e366ae6b9e8/trace/01a181c8-73e2-7462-a46c-c67ee5140197/run/01a181c8-7460-71f2-a369-db5fa43b0a42?start_time=2026-10-28T09:12:40.288843Z) mengembalikan `action=compare`, `product_ids=[digital-print-a3]`, tetapi `needs_knowledge=false`. Intent gambar Roll Up juga mengembalikan false. `app/backend/chain.py:559` mempercayainya dan melewati retrieval. Prompt classifier saat ini justru meminta true untuk setiap pertanyaan bisnis/visual; mengandalkan instruksi itu saja tidak menegakkan aturan aplikasi.

Dampak terlihat di jawaban mentah: model Roll Up meralat harga/rangka yang sebelumnya benar karena konteks kosong; model kertas menyangkal gambar dan menyebut hanya tiga pilihan dari riwayat. Validator mengembalikan `consistent=false` pada keduanya, sehingga pelanggan menerima fallback aman tetapi umum. Jadi gambar berhasil dipilih, sementara pemakaian knowledge untuk teksnya gagal; validator mencegah klaim buruk tetapi tidak memperbaiki fakta yang hilang.

Solusi langsung yang kecil adalah menegakkan kebutuhan knowledge untuk permintaan visual/business yang dikenali di kode bersama, terutama saat aplikasi sendiri meminta detail/harga setelah gambar. Untuk intent nonvisual yang tidak pasti, gunakan default mencari knowledge; skip hanya untuk respons sosial yang benar-benar tidak membutuhkan fakta. Jangan menjadikan keputusan probabilistik classifier satu-satunya sakelar akses knowledge.

### D. Anggaran reasoning menghabiskan output

[Trace generasi perbandingan](https://smith.langchain.com/o/741de134-e8d9-44cf-9caf-593fc3cb6e5e/projects/p/ac00eeb0-7d99-4513-92fe-9e366ae6b9e8/trace/01a181c8-d63d-7352-97b4-5c66f200f589/run/01a181c8-e92e-7d03-8d06-4c1c02367aff?start_time=2026-10-28T09:13:10.190082Z):

- Model jawaban `anthropic/claude-haiku-5.5`, provider OpenRouter; commit runtime `edaa20652fb37d4f303e2dd236c191faea685f8c`.
- Input 12.089 token; output 2.048, termasuk reasoning 1.886. Selisih yang tersedia untuk output non-reasoning hanya 162 token.
- `finish_reason=length`; teks berhenti pada kata “piagam”. Status trace success hanya berarti panggilan selesai, bukan jawaban lengkap.
- `app/backend/models.py:145` menetapkan 2.048 token untuk answering. Pengaturan reasoning rendah saat ini terbatas pada model structured tertentu. `app/backend/chain.py:695` mendeteksi length, tetapi pemulihan hanya berlaku untuk media response.

Dokumentasi resmi [OpenRouter reasoning tokens](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens), diambil melalui Context7, mengonfirmasi reasoning dan teks berbagi anggaran `max_tokens`/`max_completion_tokens`. Menaikkan batas tanpa mengendalikan reasoning belum menjamin output lengkap. Dukungan parameter model/provider harus diperiksa dan diuji sebelum memilih batas konkret. `reasoning.exclude` hanya menyembunyikan reasoning dan bukan solusi untuk penggunaan anggarannya.

## Rancangan solusi yang direkomendasikan

Urutan ini mengutamakan penyebab yang sudah terbukti. Tidak diperlukan pergantian vector database atau embedding untuk tahap pertama.

1. **Pulihkan kelengkapan snapshot.** Validasi source SOP yang benar, bandingkan source staged dengan manifest aktif, lalu sync melalui alur atomik yang sudah ada. Perlihatkan file yang ditambahkan/dikeluarkan dalam hasil sync agar kehilangan sumber penting mudah dikenali. Pertahankan aktivasi eksplisit dan snapshot lama saat gagal; jangan langsung membaca sumber staged untuk pelanggan.
2. **Tegakkan retrieval yang diperlukan aplikasi.** Permintaan visual yang membutuhkan detail produk tetap mencari knowledge meskipun classifier berkata false. Simpan alasan skip yang eksplisit di trace; jangan samakan nol passage dengan sapaan/menu.
3. **Utamakan cakupan fakta dalam konteks.** Pertahankan dense retrieval + rerank sebagai pencari bagian relevan. Untuk perbandingan luas, perluas ke passage dalam bagian yang sama dari versi aktif, urutkan kembali menurut dokumen, dan gunakan batas konteks. Untuk tarif, pastikan nama varian, sisi cetak, tier jumlah, unit dan angka tarif ikut bersama. Deduplicate teks identik sebelum meranking. Mulai dengan perluasan bagian deterministik; gunakan satu pencarian tambahan terarah hanya bila cakupan masih kurang. Ini lebih terarah daripada menaikkan global top-k untuk semua pertanyaan.
4. **Buat query mengikuti kebutuhan terbaru.** Gunakan fokus produk tervalidasi dan detail pesanan yang masih relevan; jangan menambahkan tiga pesan terakhir secara membabi-buta. Pisahkan kebutuhan perbandingan, rekomendasi, dan tarif ketika memang perlu. Uji A/B dengan replay sebelum mengklaim riwayat sebagai penyebab dominan. Tetap pertahankan ukuran, bahan dan jumlah untuk pesan seperti “jadi tiga”.
5. **Pastikan generasi selesai.** Atur anggaran output dan reasoning yang cocok dengan model; jangan langsung mengganti model. Perlakukan `finish_reason=length` atau output kosong sebagai hasil belum layak kirim. Buat ulang jawaban lengkap secara ringkas dari bukti terpilih dengan anggaran yang memadai; jangan menyambung fragmen mentah ke pelanggan. Jika pemulihan gagal, kirim keterbatasan yang jelas, bukan potongan kalimat.
6. **Batasi pemulihan per giliran pelanggan.** Sesuai jawaban pengguna: maksimum satu putaran pemulihan yang menambah panggilan provider, tanpa loop tak terbatas. Anggaran ini dibagi oleh pemulihan retrieval/generasi; perluasan section lokal dan dedup tidak memerlukan panggilan provider tambahan. Jika sudah terpakai dan hasil masih tidak layak, gunakan respons parsial yang menyebut bagian belum terkonfirmasi. Tetapkan deadline dan catat seluruh penggunaan token/latensi.

Untuk contoh sertifikat, jawaban yang baik membandingkan tujuh bahan secara ringkas, menjelaskan bahan yang cocok berdasarkan sumber, lalu menanyakan ukuran/sisi cetak yang belum diketahui sebelum menjanjikan total. Tarif Linen 20 lembar tersedia, tetapi “20 lembar sertifikat” belum otomatis berarti 20 lembar A3+ satu sisi. Keberhasilan retrieval tidak mengizinkan asumsi satuan atau ukuran.

## Verifikasi sebelum mengklaim stabil

- Regression offline: intent visual false tetap mengambil knowledge; pertanyaan sosial tidak memerlukan retrieval; panjang generasi length tidak dikirim mentah; pemulihan tidak berulang; versi aktif tidak bergeser di tengah giliran.
- Evidence coverage: tujuh bahan punya nama dan karakteristik lengkap dalam konteks; tarif terpilih membawa varian, unit, sisi dan tier yang benar; duplikat tidak menghabiskan slot; passage tidak diambil dari snapshot lain.
- Replay skenario awal: jam buka tanpa riwayat dan setelah cabang, nomor/alamat, harga Roll Up 2→3 buah, gambar diikuti detail, pindah produk, tujuh kertas dan sertifikat. Sertakan salah ketik bahasa Indonesia dan ganti jumlah/bahan.
- Jalankan beberapa pengulangan di model/provider yang sama untuk kasus gagal dan kontrol, pin knowledge/prompt/commit. Laporkan jumlah percobaan, jawaban lengkap, fakta tercakup, truncation, fallback, latensi dan biaya; jangan memakai trace status success sebagai ukuran kualitas.
- Mulai dari sampel kecil dengan biaya terbatas. Paid evaluation baru dijalankan saat tahap verifikasi perubahan disepakati. Jangan mengirim pesan pelanggan WhatsApp sebagai cara menjalankan replay.

## Batas bukti

Pemeriksaan ini menggunakan LangSmith MCP, query database read-only, owning source, dan reproduksi chunking offline. Pernyataan tahap investigasi tersebut mendahului implementasi. Sync dan smoke generation setelah persetujuan dicatat di bawah. Dampak rewrite query dan nilai anggaran model yang terbaik masih perlu replay; frekuensi kegagalan belum diukur. ADR baru tidak diperlukan untuk tuning yang masih reversibel; keputusan arsitektur publikasi yang sudah ada tetap berlaku.

## Implementasi setelah persetujuan

- `retrieval_context.expand_sections` melengkapi dua bagian dokumen terpilih dari records versi yang dipin. Perbandingan/harga mendapat bagian lengkap dalam batas 18.000 karakter; pertanyaan satu fakta mendapat tetangga langsung. Filter, halaman dan identitas dokumen dipertahankan. Passage tambahan diberi label Related passage, tanpa cosine palsu.
- Ranking membuang teks identik walaupun ID berbeda. Query informasi toko mengabaikan riwayat produk yang tidak diperlukan; riwayat berhenti pada pergantian topik eksplisit. Follow-up bahan/jumlah dan handoff pesanan tetap diuji.
- `requires_knowledge` mengoreksi intent false untuk permintaan bisnis/visual. Hanya pesan sepenuhnya sosial boleh melewati retrieval. Alasan retrieval dicatat dalam trace/detail jawaban.
- Answering memakai batas 4.096 token. Model OpenRouter yang diketahui mendukungnya memakai reasoning low; metadata model saat implementasi mengonfirmasi dukungan Haiku 5.5. Provider lain tidak menerima parameter reasoning OpenRouter.
- `answer_generation.generate` membuat ulang output kosong/length paling banyak sekali, memakai 8.192 token dan timeout pemulihan maksimum 20 detik dalam deadline generasi 65 detik. Retry tersembunyi SDK dimatikan. Pencarian ulang tanpa filter, bila diperlukan, memakai jatah pemulihan yang sama. Token/biaya kedua panggilan dijumlahkan; kegagalan teks tidak disimpan sebagai jawaban sukses.
- Aturan perbandingan diperjelas untuk mencegah klaim tidak cocok tanpa sumber. Nama BW/Blues White dan BC/Board Cover tidak boleh disamakan sifat/harganya tanpa bukti alias eksplisit.
- Halaman Knowledge menampilkan file yang akan masuk/keluar pada sync berikutnya. Panel evidence tidak menyamakan setiap nol-passage dengan sapaan/menu.

Perluasan dibatasi dua bagian dan anggaran karakter. Pencarian subquery adaptif belum ditambahkan karena perluasan deterministik sudah melengkapi reproduksi ini; bila replay lain masih kehilangan fakta, itu langkah berikutnya. Embedding dan dimensi tetap.

### SOP produksi

Sync dashboard berhasil pada 28 Oktober 2026 pukul 16.38.57 WIB: `kb-0f089af2f6ca4d1391185ae8d91dc790`, enam sumber, 142/142 passage terverifikasi, Up to date. Source staged yang dikelola admin digunakan apa adanya; file lokal tidak menimpa nomor/konten admin. Pertanyaan jam buka dan kontak/alamat setelah sync berhasil mengambil SOP. Ini memverifikasi pemulihan data menggunakan runtime produksi lama; kode lokal baru belum dirilis.

### Hasil verifikasi

- Suite offline final: **368 passed, 11 skipped, 2 warnings**, 65,46 detik. Paid DeepEval dilewati. Tes termasuk guard intent false, tujuh spesifikasi dan tarif Linen, filter/halaman/batas konteks, deduplikasi, perpindahan topik, pemulihan panjang/kosong, akumulasi biaya, dan HTTP nyata yang memverifikasi batas 4.096 → 8.192 saat retry.
- Frontend lint dan build lulus; warning Fast Refresh/effect yang sudah ada tetap muncul.
- Docker tidak tersedia dan port 54585 ditempati VS Code. Tes memakai PostgreSQL 15.18 sementara di loopback 54586 melalui harness `/tmp/nadhif-retrieval-pytest.py`; fixture repository tetap. Harness mengalihkan juga upstream proxy fault-injection ke server sementara. PostgreSQL 17 belum diuji. Semua database test tetap `chatbot_test_*`; tes tidak diarahkan ke Supabase produksi.
- Enam smoke generation berbayar memakai passage bisnis yang diekspor read-only dari snapshot baru dan kode lokal, tanpa akses database produksi oleh script. [Semua input/output, penggunaan token, biaya, dan trace](retrieval-generation-smoke.json) disimpan. Enam selesai `stop` tanpa pemulihan; konteks 14 passage/12.162 karakter.
- Dua smoke pertama memperlihatkan klaim perbandingan terlalu tegas; temuan itu dipakai untuk memperjelas prompt. Dua terakhir memakai pertanyaan asli, mencakup tujuh bahan, membedakan BW dari BC, dan meminta ukuran/sisi. Keduanya masih memberikan contoh hitungan berbasis lembar A3+ sebelum detail sertifikat dipastikan; contoh tersebut bukan penawaran final. Ini sampel kecil, bukan skor DeepEval atau bukti stabilitas menyeluruh.
- LangSmith MCP mengonfirmasi trace akhir memakai `max_completion_tokens=4096`, `reasoning.effort=low`, dan `finish_reason=stop`.

Customer WhatsApp dan evaluasi judge berbayar penuh tidak dijalankan. Runtime dan UI baru memerlukan deployment sebelum verifikasi end-to-end pada URL produksi.
