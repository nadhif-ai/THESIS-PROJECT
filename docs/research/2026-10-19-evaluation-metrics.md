# Riset durasi dan perbaikan metrik evaluasi RAG

**Tanggal:** 19 Oktober 2026
**Status:** Riset dan rancangan; tidak menjalankan evaluasi berbayar atau mengubah aplikasi.
**Sumber:** Dokumentasi resmi DeepEval melalui Exa MCP; dokumentasi G-Eval juga dikonfirmasi melalui Context7 `/confident-ai/deepeval`.

## Kesimpulan

Target Contextual Recall, Contextual Precision, dan Business correctness di atas 0,85 layak dijadikan **kriteria penerimaan yang harus diuji**, tetapi tidak dapat dijamin dengan mengganti satu parameter. Urutan yang masuk akal adalah memperbaiki acuan dan validitas penilaian, merapikan bukti knowledge, memperbaiki retrieval tanpa reranking, lalu memvalidasi perhitungan serta perilaku klarifikasi.

Screenshot pengguna memuat Faithfulness 93%, Answer Relevancy 99%, Contextual Recall 72%, Contextual Precision 73%, dan Business correctness 75%, untuk 10 kasus, chunking 1.500/200. Angka tersebut adalah agregat skor metrik; **75% G-Eval bukan bukti bahwa tepat 75% transaksi bisnis benar**. Penilaian LLM perlu diperiksa pada contoh konkret, dan 10 kasus belum mewakili seluruh variasi pertanyaan pelanggan. [Dokumentasi G-Eval](https://deepeval.com/docs/metrics-llm-evals).

## Apa yang sebenarnya diukur

| Metrik | Arti dan implikasi |
| --- | --- |
| Contextual Recall | Menilai berapa banyak pernyataan dalam `expected_output` yang dapat didukung oleh `retrieval_context`. Acuan yang kedaluwarsa, terlalu luas, atau menuntut angka turunan tanpa menjelaskan bukti perhitungannya dapat menyulitkan interpretasi skor. Perbaiki fakta acuan dan bukti yang benar-benar diperlukan sebelum menyimpulkan seluruh kehilangan skor berasal dari retriever. |
| Contextual Precision | Menilai apakah konteks yang relevan terhadap pertanyaan dan jawaban acuan berada di urutan atas. Perhitungannya berupa weighted cumulative precision; ini bukan sekadar jumlah chunk relevan dibagi top-k. Contoh konseptual: jika satu-satunya konteks relevan muncul pada urutan kelima, skor precision berbasis urutan dapat sekitar 0,2. |
| Business correctness [G-Eval] | Metrik kustom berdasarkan kriteria, parameter kasus, dan jawaban acuan. Hasilnya bergantung pada ketepatan acuan serta pemahaman judge terhadap harga, satuan, jumlah, kondisi, dan klarifikasi yang dibenarkan. G-Eval secara resmi tidak deterministik. |

Definisi dan mekanisme: [Contextual Recall](https://deepeval.com/docs/metrics-contextual-recall), [Contextual Precision](https://deepeval.com/docs/metrics-contextual-precision), [G-Eval](https://deepeval.com/docs/metrics-llm-evals).

Recall dan precision sama-sama memakai `expected_output`; mengoreksi jawaban acuan dapat mengubah skor tanpa perubahan retrieval. Karena itu hasil lama harus tetap disimpan, dan baseline perlu dievaluasi ulang dengan dataset terkoreksi yang sama jika dipakai untuk perbandingan ilmiah. Skor dari dua definisi metrik yang berbeda tidak boleh diberi nama atau diperlakukan sebagai benchmark yang setara. [Contextual Recall](https://deepeval.com/docs/metrics-contextual-recall), [Contextual Precision](https://deepeval.com/docs/metrics-contextual-precision).

## Durasi: tidak ada angka normal universal

Dokumentasi resmi yang diperiksa tidak memberikan SLA untuk tepat 10 kasus RAG dengan lima metrik. Sepuluh kasus menghasilkan **50 penilaian kasus–metrik**, tetapi tidak otomatis berarti 50 panggilan judge: metrik dapat memiliki beberapa tahap model, alasan penilaian, pembuatan langkah G-Eval, retry, dan cache. [Pengantar evaluasi](https://deepeval.com/docs/evaluation-introduction), [G-Eval](https://deepeval.com/docs/metrics-llm-evals).

Model mental yang berguna:

`durasi total = waktu antre/terhenti + generasi jawaban + penilaian judge + retry + dispatch/checkpoint`

Dengan eksekusi paralel, bagian kerja yang independen dapat tumpang tindih; menjumlahkan waktu setiap request tidak lagi sama dengan wall-clock. Python `AsyncConfig` mendukung evaluasi asinkron, `max_concurrent`, dan `throttle_value`. Dokumentasi saat diperiksa menyebut default Python `max_concurrent=20`; itu bukan rekomendasi untuk langsung mengirim 20 pekerjaan ke provider dan bukan bukti bahwa executor durable project memakai concurrency tersebut. Bagian TypeScript di halaman yang sama menjelaskan penjadwalan berbeda. Cocokkan versi terpasang dan jalur executor nyata. [Flags and Configs](https://deepeval.com/docs/evaluation-flags-and-configs#async-configs).

**Bukti project dari investigasi utama:** estimasi insiden terkait adalah sekitar 16 menit waktu aktif, termasuk sekitar 104 detik akumulasi sepuluh generasi jawaban. Wall-clock sekitar 129 menit mencakup interval worker berhenti; sisa pekerjaan setelah dipulihkan ke cloud selesai sekitar 70 detik. Angka ini rekonstruksi insiden, bukan SLA, dan bukan bukti bahwa 10 kasus penuh normalnya selesai dalam 70 detik. **Usulan target setelah optimasi, belum benchmark:** 5–10 menit untuk sepuluh kasus dengan recipe dan model yang sama. Gunakan histori beberapa run lengkap untuk menyusun p50/p95. Ini sasaran rekayasa, bukan angka normal resmi DeepEval atau janji provider.

Optimasi yang tidak mengganti arti metrik:

1. Catat waktu generasi, tiap tahap metrik/judge, checkpoint, queue, retry, serta 429/timeout; tampilkan umur checkpoint terakhir dan status worker.
2. Pin `evaluation_steps` G-Eval yang sudah direview sehingga tidak perlu meminta model menyusun langkah baru pada setiap instance; tetap gunakan kriteria bisnis yang sama. Langkah eksplisit meningkatkan kontrol/konsistensi, bukan menjamin determinisme. [G-Eval](https://deepeval.com/docs/metrics-llm-evals).
3. Uji concurrency kecil dan terbatas untuk pekerjaan independen sesuai kuota judge. Jangan menambahkan fan-out tanpa menjaga checkpoint, deadline, lease, idempotensi, dan pemulihan yang sudah ada. `AsyncConfig` saja tidak otomatis memparalelkan loop executor kustom. [Flags and Configs](https://deepeval.com/docs/evaluation-flags-and-configs#async-configs).
4. Gunakan hasil checkpoint untuk melanjutkan sisa pekerjaan; cache hanya sah ketika isi kasus, retrieval, konfigurasi metrik, dan model tidak berubah. [Cache Configs](https://deepeval.com/docs/evaluation-flags-and-configs#cache-configs).

## Prioritas perbaikan kualitas tanpa reranking

### 1. Audit acuan dan judge terlebih dahulu

Untuk tiap kasus, pisahkan fakta sumber, angka yang harus dihitung, spesifikasi yang belum diberikan pelanggan, dan informasi opsional. Gunakan kebijakan bisnis yang telah dikonfirmasi; jangan mempertahankan acuan yang bertentangan dengan knowledge aktif hanya demi kontinuitas skor. Jika mengoreksi acuan, simpan dataset lama dan beri identitas/checksum baru.

Catatan audit run project dari investigasi utama menunjukkan perlunya pemeriksaan ini: referensi DP masih menyebut 50–60% sementara kebijakan yang terambil 60%; pertanyaan banner tidak menyebut kualitas tetapi acuan memaksakan harga standar, sedangkan bot meminta klarifikasi; beberapa alasan recall menyebut fakta atau nomor node yang tidak sesuai dengan artefak kasus. Temuan tersebut perlu dilabeli sebagai masalah acuan/judge, terpisah dari kegagalan retrieval nyata. Itu bukan alasan menghapus semua skor rendah.

Kalibrasikan judge terhadap penilaian manusia dengan contoh: benar lengkap, benar dengan klarifikasi, salah harga, salah satuan, salah jumlah, dan jawaban tanpa dukungan. Bekukan judge dan langkah penilaian setelah kalibrasi. Untuk G-Eval, dokumentasi menyediakan `evaluation_steps` dan rubric yang rentang skornya tidak tumpang tindih. Hanya parameter yang disebut dalam instruksi penilaian yang perlu disertakan. [G-Eval](https://deepeval.com/docs/metrics-llm-evals).

Dokumentasi menjelaskan bahwa adapter custom yang tidak menyediakan raw response/logprobs dapat memakai skor integer mentah, bukan probability-weighted score. **Jangan menganggap ini otomatis terjadi pada run project:** `OpenRouterJudge` mewarisi `OpenRouterModel`; kemampuan metode turunan dan dukungan provider pada versi terpasang perlu diperiksa dahulu. [Custom logprobs untuk G-Eval](https://deepeval.com/docs/metrics-llm-evals#how-is-it-calculated).

### 2. Buat satu blok sumber cukup untuk satu keputusan bisnis

Satukan nama bahan, varian, satuan harga, rentang kuantitas, minimum order, sisi cetak, finishing, dan syarat yang memengaruhi harga. Ulangi heading atau identitas produk pada setiap potongan tabel yang terpisah. Hindari passage hanya separator, duplikasi tarif, dan tabel yang kehilangan header saat ekstraksi PDF. Format PDF tidak dengan sendirinya meningkatkan retrieval; hasil teks/tabel yang masuk index tetap harus diperiksa.

Ini rekomendasi project berdasarkan kebutuhan bukti pada Recall dan relevansi urutan pada Precision, bukan ukuran chunk universal dari DeepEval. [Contextual Recall](https://deepeval.com/docs/metrics-contextual-recall), [Contextual Precision](https://deepeval.com/docs/metrics-contextual-precision).

### 3. Tuning retrieval satu faktor setiap eksperimen

Pertahankan 1.500/200 sebagai kontrol. Kandidat praktis berikutnya: 800/80, 1.000/100, dan 1.200/120 dengan pemisahan per bagian/tabel, **top-k tetap 5** selama eksperimen chunking. Setelah memilih chunking, bandingkan top-k 3, 5, dan 7 dengan chunking tersebut tetap. Ukuran tersebut kandidat uji, bukan nilai optimum yang sudah terbukti untuk Nemotron saat ini.

Tanpa reranking, coba normalisasi istilah yang terkontrol, misalnya `bolak-balik` → `dua sisi / 2S`, `kisscut` → `kiss cut`, dan pemilihan kategori berdasarkan intent bila klasifikasinya dapat dipercaya. Jangan memaksa filter sempit ketika intent tidak jelas. Ukur apakah passage yang memuat tarif/kebijakan yang benar naik pada hasil pencarian, bukan hanya apakah nama file cocok. Menaikkan top-k saja dapat membantu recall sambil menambah noise dan biaya; mengecilkan top-k saja dapat meningkatkan precision sambil menghilangkan fakta wajib. [Contextual Recall](https://deepeval.com/docs/metrics-contextual-recall), [Contextual Precision](https://deepeval.com/docs/metrics-contextual-precision).

### 4. Validasi angka dan kebijakan klarifikasi

Untuk kebutuhan bisnis yang bisa dihitung, gunakan pemeriksaan deterministik terpisah: harga per unit, jumlah lembar, pembulatan, total, minimum order, dan kapasitas yang tidak sama dengan jumlah produk yang dijanjikan. Pastikan kebijakan klarifikasi diterima ketika spesifikasi penting memang belum diberikan. G-Eval dapat tetap menilai jawaban keseluruhan, tetapi tidak menjadi satu-satunya bukti kebenaran aritmetika karena ia tidak deterministik. [G-Eval](https://deepeval.com/docs/metrics-llm-evals).

Checker deterministik tidak boleh dilaporkan sebagai skor **Business correctness [G-Eval]** yang sama. Jika nanti diterapkan, tampilkan nama, formula, versi recipe, serta baseline tersendiri; jangan menukar metrik demi memperoleh persentase lebih tinggi.

## Protokol pembuktian target >85%

1. Pertahankan hasil run lama dan artefaknya. Bekukan dataset yang sudah dikoreksi, corpus aktif, prompt, embedding/index, judge, dan definisi metrik.
2. Jalankan baseline pada dataset terkoreksi dan labeli terpisah dari baseline historis.
3. Pilih satu perubahan retrieval per eksperimen, lalu bandingkan semua kandidat dengan acuan dan evaluator identik.
4. Laporkan rata-rata tiga metrik beserta skor per kasus, kegagalan harga/kuantitas/policy, dan waktu kerja/antrean. Jangan menyembunyikan kasus gagal di balik agregat.
5. Setelah memilih konfigurasi, validasi pada pertanyaan baru yang tidak dipakai untuk tuning dan direview manusia. Gunakan sekitar 30–50 kasus sebagai sasaran praktis awal project; bukan jaminan kecukupan statistik atau angka baku universal.
6. Jika judge atau definisi metrik berubah, lakukan kalibrasi dan baseline baru; jangan mengklaim kenaikan sebagai perbaikan retriever sebelum dinilai dengan alat ukur yang sama.

Target diterima hanya bila kenaikan precision tidak menurunkan cakupan fakta penting dan kenaikan skor bisnis tidak berasal dari melonggarkan acuan. Tidak ada eksperimen atau skor baru yang dihasilkan oleh catatan riset ini.
