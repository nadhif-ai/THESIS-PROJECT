# Riset chunking untuk knowledge base kecil

**Tanggal:** 12 Oktober 2026  
**Status:** Riset selesai; implementasi dan benchmark retrieval draft dilakukan setelah persetujuan pengguna. Bagian riset di bawah merekam keadaan sebelum implementasi; hasil terbaru ada pada bagian terakhir. Evaluasi jawaban dengan judge belum diulang.

## Ringkasan

- Tidak ada ukuran chunk universal yang paling baik. Hasil bergantung pada apakah jawaban ada dalam satu fakta lokal atau perlu konteks beberapa kalimat, struktur sumber, dan tokenizer embedding.
- Untuk corpus cetak yang mayoritas berisi harga, spesifikasi, dan langkah singkat, **1.000 karakter dengan overlap 100** layak menjadi kandidat pertama untuk diuji. Ini kandidat, bukan hasil optimum.
- Karena keluhan utamanya precision, bandingkan kandidat itu dengan **1.000/0** untuk melihat apakah overlap menambah passage duplikat, serta **800/80** untuk melihat apakah chunk lebih sempit meningkatkan relevansi passage. Pertahankan **1.500/200** sebagai kontrol lama.
- PDF tidak otomatis meningkatkan retrieval. PDF yang dapat diekstrak tetap diubah menjadi teks dan mengikuti pemisahan yang sama. Gunakan format yang mempertahankan tabel/heading dengan benar, lalu nilai hasil ekstraksinya.

## Yang ada sekarang

`RecursiveCharacterTextSplitter` menghitung panjang secara default dengan karakter, memprioritaskan separator agar paragraf dan kalimat tidak terpotong, dan menganggap overlap sebagai target. LangChain merekomendasikan splitter rekursif ini untuk teks generik; dokumentasinya memberi contoh `1.000/200`, tetapi contoh tersebut bukan aturan optimum untuk corpus ini. [Dokumentasi splitter LangChain](https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter) dan [dokumentasi pemecahan knowledge base](https://docs.langchain.com/oss/python/langchain/knowledge-base).

Loader project saat ini memakai `1.500/200` dan separator heading, paragraf, baris, kalimat, lalu spasi. Data snapshot awal terdiri dari lima berkas TXT terindeks, sekitar 90.918 karakter. Model `intfloat/multilingual-e5-small` menerima prefix `passage:` untuk dokumen, berdimensi 384, dan input panjang dipotong pada 512 token; model card meminta prefix `query:` dan `passage:` untuk retrieval, termasuk bahasa non-Inggris. [Model card multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small).

Pengukuran tokenizer lokal pada source TXT snapshot dengan prefix dan special token:

| Chunk / overlap karakter | Jumlah chunk | Median token | P95 token | Maksimum token | Chunk > 512 token |
|---|---:|---:|---:|---:|---:|
| 1.500 / 200 (sekarang) | 95 | 282 | 433 | 552 | 2 |
| 1.000 / 100 | 156 | 184 | 303 | 361 | 0 |
| 800 / 80 | 190 | 149 | 234 | 301 | 0 |
| 1.000 / 0 | 156 | 182 | 302 | 361 | 0 |

Pemeriksaan isi yang tersimpan di snapshot indeks mengonfirmasi dua passage saat ini melebihi batas model: indeks 2 dan 5 dari `06_estimasi_pcs_per_lembar_a3.txt` berukuran 552 dan 549 token. Akibatnya, akhiran passage itu berisiko tidak ikut terwakili dalam embedding. Statistik kandidat pada tabel berasal dari source TXT sebelum normalisasi isi loader (termasuk pembersihan marker media); jumlah dan distribusi indeks setelah normalisasi perlu dihitung ulang saat ada eksperimen. Ini hanya pemeriksaan ukuran/tokenizer, bukan evaluasi kualitas retrieval.

## Bukti dan batas penerapannya

- Studi retrieval QA lintas dataset menemukan bahwa chunk kecil lebih cocok pada pertanyaan dengan jawaban fakta singkat, sedangkan chunk besar dapat membantu saat bukti tersebar atau konteks teknis lebih luas. Hasilnya berbeda antar dataset dan model embedding. Studi itu memakai ukuran token, dua model embedding selain model project ini, dan beberapa corpus panjang yang sebagian dibentuk dengan menggabungkan dataset QA; angka ukurannya tidak bisa dipindahkan langsung ke dokumen percetakan kita. [Bhat dkk., *Rethinking Chunk Size for Long-Document Retrieval* (2026, preprint)](https://arxiv.org/abs/2505.21700).
- Studi retrieval ilmiah khusus kimia yang mencakup E5 menguji chunk rekursif berbasis token dan berbagai overlap; penulis melaporkan low/no overlap umumnya menguntungkan, sementara overlap dapat menambah recall kecil tetapi menurunkan precision dan memperbesar indeks. Ini bukti pendukung untuk menguji overlap rendah, bukan resep langsung: corpus, label, model, dan tugasnya berbeda dari katalog usaha percetakan. [Amiri & Bocklitz, *Chunk Twice, Embed Once* (versi 2, 2026, preprint)](https://arxiv.org/abs/2506.17277v2).
- DeepEval **Contextual Precision** menilai apakah konteks yang relevan terhadap pertanyaan dan jawaban ideal berada di urutan atas; **Contextual Recall** memeriksa seberapa banyak pernyataan pada jawaban ideal didukung oleh retrieval context. Keduanya memerlukan `expected_output` dan `retrieval_context`, sehingga jawaban acuan perlu diaudit dahulu. **Contextual Relevancy** bersifat opsional untuk mengukur banyaknya sinyal relevan terhadap pertanyaan dalam konteks yang diambil, tanpa membutuhkan jawaban acuan. Nilai-nilai ini adalah penilaian LLM-as-a-judge dan perlu spot-check manusia. [Contextual Precision](https://deepeval.com/docs/metrics-contextual-precision), [Contextual Recall](https://deepeval.com/docs/metrics-contextual-recall), [Contextual Relevancy](https://deepeval.com/docs/metrics-contextual-relevancy).

## Urutan perbaikan yang disarankan

### Audit run terbaru yang tersedia

Run lokal `data/evaluations/21b17772fbab41dc8fbc7f0a26edecd2/results.json`, dimulai 12 Oktober 2026 pukul 14.47 WIB, memakai versi `draft-ffa4eb9c27fb`. Rata-rata judge: Faithfulness 0,98; Answer Relevancy 0,795; Business Correctness 0,576. Ini run yang berbeda dari laporan Pinecone sebelumnya (`26653d0a3fc344d3ad59129592a2e1bb`, Business Correctness 0,57); keduanya tidak boleh dianggap sebagai eksperimen konfigurasi chunking yang berbeda.

| Kasus | Bukti | Implikasi rancangan |
|---|---|---|
| 5: banner Flexi 280 ukuran 2×1 m | Konteks hasil retrieval memuat passage `---` dan Roll Up Banner, sementara harga yang diperlukan tersedia di `dataset/knowledge_base/04_daftar_estimasi_harga.txt:14` dan rumus di baris 934–935. | Kegagalan retrieval nyata. Audit passage yang hanya berupa separator; pertahankan nama bahan, harga, dan satuan dalam satu blok. |
| 3: stiker tahan air | Konteks harga relevan terambil, tetapi jawaban berakhir pada `Rp 12.500/`. | Jawaban tampak terpotong. Periksa trace/finish reason/budget output sebelum menyimpulkan bahwa chunking penyebabnya. |
| 8: stiker 5×5 cm per A3+ | Jawaban berakhir pada `muat <b>`, meskipun konteks terkait terambil. Sumber `03_panduan_berkas_siap_cetak.txt:122` menyebut Kiss Cut 35; `06_estimasi_pcs_per_lembar_a3.txt:42` menyebut mesin 40 dan manual 54. | Konflik sumber dan keluaran tidak lengkap. Konfirmasi kondisi pemotongan/area/spacing bisnis sebelum memilih angka acuan; jangan otomatis mengganti salah satu angka untuk menaikkan skor. |
| 7 dan 9: total harga | Referensi kasus 7 mengasumsikan kualitas standar; kasus 9 mengasumsikan Art Carton tanpa laminasi, sementara pertanyaan tidak menyebut seluruh pilihan itu. Jawaban meminta klarifikasi. | Tetapkan kebijakan default atau klarifikasi secara eksplisit. Jika pilihan memang memengaruhi harga dan belum diberikan, rubric perlu menerima klarifikasi yang tepat. |

Angka judge bukan akurasi bisnis yang sudah divalidasi manusia. Bukti di atas memerlukan review isi; tidak ada goldens atau harga yang diubah dalam tahap riset. File dataset acuan: `testing/test_dataset.csv`, kasus 3/5/7/8/9. Konfigurasi chunking aktif berada di `app/admin/knowledge.py:146`; belum disimpan sebagai konfigurasi per versi knowledge.

### Rancangan langkah 1–4

1. **Audit jawaban acuan dan contoh gagal.** Untuk tiap pertanyaan, tetapkan fakta yang wajib untuk menjawabnya dan fakta yang hanya opsional. Pastikan harga menyebut satuan, ukuran/varian, biaya tambahan, dan syarat yang benar. Jangan menganggap jawaban kurang lengkap hanya karena tidak memuat detail yang tidak diminta. Periksa apakah passage yang dinilai relevan benar-benar dapat membantu menjawab pertanyaan; nama file saja belum cukup sebagai label relevansi.
2. **Tambahkan metrik retrieval ke laporan DeepEval.** Catat Contextual Precision dan Contextual Recall bersama metrik jawaban yang sudah ada; tambahkan Contextual Relevancy hanya sebagai diagnostik noise bila membantu. Tetap simpan skor benchmark lama secara terpisah untuk perbandingan historis. Metrik LLM menilai konteks berdasarkan referensi, sehingga audit referensi mendahului interpretasi skor.
3. **Rapikan knowledge sebelum tuning chunk.** Satukan dalam satu blok semantik nama produk/bahan, ukuran atau varian, harga beserta satuannya, finishing, minimum order, dan syarat yang mengubah harga. Pertahankan heading dan baris tabel yang bermakna. PDF cocok bila itulah sumber bisnis kanonis dan teks/tabelnya terekstrak utuh; mengganti TXT menjadi PDF saja tidak menambah informasi retrieval. Loader project memakai `PyPDFLoader`, lalu splitter teks yang sama: [loader project](../../app/backend/loader.py).
4. **Bandingkan konfigurasi pada corpus dan goldens yang dibekukan.** Gunakan kontrol `1.500/200`, kandidat `1.000/100`, ablation overlap `1.000/0`, dan pembanding lebih kecil `800/80`. Jaga model, top-k, prompt, judge, pertanyaan, dan jawaban acuan tetap sama. Ukur konteks hasil retrieval termasuk jumlah token prompt: top-k tetap tidak berarti total token konteks tetap, jadi perubahan skor tak boleh langsung dianggap akibat ukuran chunk saja. Buat setiap konfigurasi sebagai versi indeks terpisah dan jangan memublikasikan versi eksperimen sebelum ditinjau.

Tidak ada target skor yang dijamin. Jika precision naik tetapi fakta penting hilang dari konteks, konfigurasi tersebut belum memenuhi kebutuhan jawaban bisnis yang lengkap. Tidak ada reranking dalam lingkup riset ini.

Untuk tahap implementasi berikutnya, simpan ukuran chunk, overlap, separator, versi corpus, dan hash jawaban acuan dalam manifest eksperimen. Bekukan referensi asli sebagai baseline historis; gunakan versi referensi yang direview untuk membandingkan **seluruh** kandidat, termasuk kontrol lama, agar perbaikan label tidak disalahartikan sebagai perbaikan retrieval. Review separator kosong dan blok harga dilakukan lebih dahulu, lalu corpus hasil review dibekukan untuk semua konfigurasi. Dengan empat konfigurasi dan sepuluh pertanyaan awal terdapat 40 keluaran untuk dibandingkan; biaya judge bergantung metrik dan provider, dan belum dijalankan di tahap riset. Data held-out percakapan digunakan setelah konfigurasi dipilih, bukan untuk memilih konfigurasi. Pemeriksaan lokal panjang chunk/token di atas tidak memakai API model.

## Implementasi dan hasil retrieval draft

Konfigurasi karakter disimpan per versi knowledge; default draft dari versi historis adalah 1.000/100. Preprocessing `sections-v1` memisahkan bagian berdasarkan heading, menyertakan hierarki heading pada tiap passage, dan membuang separator tanpa isi. Batas karakter juga menghitung heading yang ditambahkan. Overlap berlaku di dalam bagian. Semua passage dihitung dengan tokenizer E5 sebelum embedding; draft yang memiliki passage di atas 512 token ditolak untuk mencegah truncation diam-diam. Snapshot historis tetap tersedia dan tidak dibangun ulang.

| Konfigurasi | Passage hasil preprocessing | Maksimum token | Hit Rate@3 | Source-file Precision@3 | Versi |
|---|---:|---:|---:|---:|---|
| Historis 1.500/200 | 95 | 552 | 90% | 60% | `draft-ffa4eb9c27fb` (versi published saat eksperimen) |
| Section 1.500/200 | 99 | 595 | — | — | Ditolak: 2 passage melewati batas token |
| Section 1.000/100 | 139 | 371 | 100% | 86,7% | `draft-bfe0f4418893` |
| Section 800/80 | 173 | 328 | 100% | 80% | `draft-0f2f3f2a451e` |
| Section 1.000/0 | 136 | 371 | 100% | 80% | `draft-097b705be850` |

Artifact: `testing/comparisons/2026-10-12-chunking-retrieval.json`; audit ukuran lokal: `testing/comparisons/chunking-candidates.json`. Corpus yang sama berasal dari versi published yang dipilih di awal, dan hash file disimpan. Query benchmark 10 pertanyaan asli, k=3, tanpa filter metadata, embedding E5 dan Pinecone; script tidak memanggil model jawaban/judge. Nama file tetap menjadi label relevansi yang kasar. Kasus harga Flexi (5) sekarang mengambil tiga passage dari sumber harga pada ketiga kandidat baru.

Peningkatan dibanding baseline juga mencakup preprocessing; bukan bukti kausal ukuran chunk saja. Kandidat 1.000/100 paling tinggi pada benchmark kecil ini, belum terbukti terbaik pada percakapan atau jawaban harga. Tidak ada versi eksperimen yang dipublikasikan oleh proses ini.

`testing/evals/qa-reference-candidates.json` menyalin pertanyaan/referensi lama sebagai kandidat review, menghapus jam buka yang tidak wajib pada pertanyaan alamat, dan menambahkan panduan klarifikasi pada kasus 7/9. Referensi asli tetap utuh. Kasus 8 berstatus **hold atas permintaan pengguna**, menunggu konfirmasi kondisi pemotongan; review baru mencakup 9 kasus non-held. Review manusia belum ditandai otomatis. Dashboard menyediakan review terpisah dan pembatalan berdasarkan checksum.

Contextual Precision dan Contextual Recall sudah ditambahkan ke evaluator QA dan feedback LangSmith. Konfigurasi model/judge/top-k dibekukan per run; hasil mencatat konfigurasi chunking dan hash corpus/dataset. Hasil jawaban yang tampak terpotong tetap membutuhkan pemeriksaan trace; budget output/model tidak diubah dalam pekerjaan chunking ini. Build frontend dan kompilasi Python dilakukan; suite test dan evaluasi judge baru belum dijalankan.

## Koreksi bisnis setelah konfirmasi pengguna

Pengguna mengonfirmasi **Kiss Cut 5×5 cm = 35 pcs per lembar A3+**. Kasus 8 dilepas dari hold; referensi QA saat ini dan kandidat audit memakai nilai 35 dengan sumber kanonis `03_panduan_berkas_siap_cetak.txt`. Jumlah potong manual bukan jawaban acuan untuk kasus ini. Dataset baseline, vector snapshot, dan hasil eksperimen lama tetap merupakan rekaman historis. Script benchmark historis membaca label sumber dari CSV baseline beku agar koreksi label saat ini tidak diam-diam mengubah pembanding.

Kolom/tabel Kiss Cut duplikat di dokumen 06 dihapus, sementara informasi unik potong manual dipertahankan. Panduan harga 04 membatasi rumus grid untuk potong manual dan mengarahkan Kiss Cut ke tabel resmi; contoh Kiss Cut yang bertentangan dengan tabel resmi dihapus. Di dokumen 03, baris 5×5 dipindah menjadi satu bagian khusus dengan pertanyaan/jawaban lengkap, sehingga fakta tidak diduplikasi di dalam sumber.

Draft koreksi **`draft-ca03c96c8b14`**, 1.000/100, berisi 139 passage. Retrieval k=5 untuk pertanyaan kasus 8 mengembalikan bagian kanonis dengan **35 pcs** pada urutan pertama. Artifact: `testing/comparisons/2026-10-12-kiss-cut-correction.json`. Ini pemeriksaan retrieval, bukan scoring judge atau pengujian pengiriman WhatsApp. Draft tidak dipublikasikan otomatis.

Kandidat percakapan hasil generation sebelumnya memuat konteks dari tabel lama. Status stale berdasarkan checksum mencegah review/scoring kandidat lama sampai konteks dan expected outcome dikoreksi atau dibuat ulang. Tidak ada generation atau evaluasi berbayar baru yang dijalankan untuk koreksi ini.
