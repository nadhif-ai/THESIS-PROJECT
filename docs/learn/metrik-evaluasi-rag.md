# Memahami lima metrik evaluasi chatbot RAG

Panduan ini menjelaskan lima metrik pada hasil evaluasi dashboard: **Faithfulness, Answer Relevancy, Contextual Recall, Contextual Precision, dan Business correctness [GEval]**. Tujuannya agar angka yang tampil dapat dijelaskan dengan bahasa sederhana, termasuk bagian yang dihitung menggunakan rumus dan bagian yang diputuskan oleh model penilai.

**Catatan versi:** kelima metrik tersebut terdapat pada hasil historis yang ditunjukkan dalam gambar. Evaluasi QA baru menggunakan empat metrik: Faithfulness, Answer Relevancy, Contextual Recall, dan Contextual Precision. Business correctness G-Eval tidak dijalankan pada run baru. Ekspor hasil lama tetap mempertahankan metrik aslinya; dashboard menampilkan empat metrik QA yang tersedia tanpa mengubah bukti tersimpan. Penjelasan perbedaan protokol tersedia di [bagian perubahan protokol](#perubahan-protokol-pada-project-ini).

Semua contoh harga, keputusan penilai, dan angka perhitungan di bawah adalah **ilustrasi pembelajaran**, bukan tarif resmi toko atau hasil pengujian baru. Angka 93%, 99%, 72%, 73%, dan 75% pada bagian pembacaan dashboard mengikuti gambar pengguna.

## Gambaran singkat

| Metrik | Pertanyaan yang dijawab | Fokus pemeriksaan |
| --- | --- | --- |
| Faithfulness | Apakah klaim dalam jawaban selaras dengan konteks yang diterima chatbot? | Jawaban dibandingkan dengan konteks retrieval. |
| Answer Relevancy | Apakah isi jawaban membahas pertanyaan pengguna? | Pernyataan jawaban dibandingkan dengan pertanyaan. |
| Contextual Recall | Apakah konteks yang ditemukan mencakup informasi yang diperlukan oleh jawaban acuan? | Pernyataan acuan dibandingkan dengan konteks retrieval. |
| Contextual Precision | Apakah potongan konteks yang relevan berada di urutan atas? | Relevansi dan peringkat konteks. |
| Business correctness [GEval] | Apakah jawaban memenuhi kriteria usaha, termasuk harga, satuan, jumlah, syarat, dan perhitungan? | Penilaian rubrik kustom terhadap jawaban. |

Faithfulness dan Answer Relevancy terutama membantu membaca kualitas jawaban. Contextual Recall dan Contextual Precision membantu membaca kualitas retrieval. Business correctness melengkapi pemeriksaan dengan kebutuhan khusus usaha digital printing.

Kelima skor tidak perlu dirata-ratakan lagi menjadi satu angka keberhasilan. Masing-masing menjelaskan masalah yang berbeda.

## Istilah RAG yang perlu dipahami

| Istilah | Arti sederhana | Contoh atau kaitannya dengan project |
| --- | --- | --- |
| RAG | Cara membuat jawaban dengan mengambil informasi dari sumber terlebih dahulu, kemudian menyertakannya kepada LLM. | Chatbot mencari informasi produk sebelum menyusun jawaban WhatsApp. |
| Knowledge base | Kumpulan sumber informasi yang dipakai sistem. | Dokumen produk, harga, bahan, dan kebijakan toko. |
| Corpus atau korpus | Keseluruhan kumpulan dokumen atau teks dalam suatu konfigurasi penelitian. | Korpus yang sama diperlukan ketika membandingkan dua cara chunking. |
| Document | Satu dokumen sumber, yang dapat memiliki banyak potongan. | Satu PDF daftar produk dapat menghasilkan beberapa chunk. |
| Chunk | Potongan teks hasil pemecahan dokumen. | Bagian tentang harga banner dipisahkan dari bagian kebijakan pembayaran. |
| Passage | Unit teks yang disimpan atau dikembalikan oleh retriever. Dalam project ini, biasanya berupa chunk yang sudah diproses, terkadang dengan tambahan judul atau identitas bagian. | Lima hasil retrieval berarti lima passage, bukan selalu lima dokumen berbeda. |
| Chunking | Proses membagi dokumen menjadi chunk. | Pengaturan `1500/200` menunjukkan ukuran chunk dan overlap dalam karakter pada konfigurasi terkait. |
| Overlap | Bagian teks yang diulang di antara chunk yang berdekatan. | Overlap dapat menjaga sambungan informasi, tetapi juga mengulang fakta yang sama. |
| Query | Pertanyaan atau teks pencarian yang digunakan untuk mengambil informasi. | “Berapa biaya banner ukuran 2 × 1 meter?” |
| Embedding | Representasi teks dalam bentuk deretan angka agar kemiripan makna dapat dibandingkan. | Project menggunakan embedding Nemotron melalui OpenRouter. |
| Dimensi embedding | Banyaknya komponen angka dalam satu vektor embedding. | `2048` dimensi berarti 2.048 komponen angka; bukan 2.048 karakter, token, atau passage. |
| Vector store | Penyimpanan vektor dan metadata untuk pencarian kemiripan. | Pinecone menyimpan vektor passage. |
| Cosine similarity | Ukuran kemiripan arah dua vektor. | Kemiripan vektor membantu memilih kandidat passage; nilainya bukan skor kebenaran jawaban. |
| Retriever | Komponen yang mengambil passage yang dianggap sesuai dengan query. | Mengembalikan daftar konteks dari Pinecone. |
| Top-k | Batas jumlah hasil yang diminta dari retriever. | `k = 5` berarti meminta hingga lima passage. Ini berbeda dari jumlah metrik evaluasi. |
| Rank atau peringkat | Posisi passage dalam hasil retrieval. | Rank 1 adalah hasil pertama; rank 5 adalah hasil kelima. |
| Retrieval context | Daftar passage hasil retrieval yang menjadi bukti untuk menyusun atau menilai jawaban. | Disimpan sebagai `retrieval_context` pada kasus evaluasi. |
| Context window | Batas masukan yang dapat ditangani model, biasanya dinyatakan dalam token. | Harus menampung instruksi, konteks, pertanyaan, dan bagian riwayat percakapan. Berbeda dari jumlah passage. |
| Prompt | Instruksi beserta informasi yang diberikan kepada model. | Mengarahkan chatbot memakai sumber dan meminta klarifikasi bila spesifikasi kurang. |
| Token | Unit teks yang diproses model. | Satu token tidak selalu sama dengan satu kata atau satu karakter. |
| Generation | Tahap menyusun jawaban setelah konteks ditemukan. | LLM menjelaskan harga atau menanyakan spesifikasi pesanan. |
| Actual output | Jawaban yang benar-benar dihasilkan chatbot pada pengujian. | Disimpan dalam hasil project sebagai `answer`, lalu dikirim ke DeepEval sebagai `actual_output`. |
| Expected output | Jawaban acuan yang digunakan dalam evaluasi. | Berasal dari `ground_truth` pada data QA. Acuan tetap perlu diperiksa ketepatannya. |
| Claim dan statement | Klaim faktual atau pernyataan yang dipisahkan untuk dinilai. | “Harga per meter persegi adalah Rp20.000” merupakan satu klaim. Pemisahannya oleh judge tidak selalu mengikuti jumlah kalimat atau tanda titik. |
| Judge | Model penilai yang memeriksa jawaban atau konteks. | Berbeda peran dari model yang menghasilkan jawaban pelanggan. |
| Verdict | Keputusan judge terhadap satu item. | Misalnya `yes`, `no`, atau `borderline`, sesuai jenis metrik. |
| Snapshot dan namespace | Snapshot merekam keadaan pengetahuan tertentu; namespace memisahkan kelompok vektor di Pinecone. | Hasil evaluasi harus dikaitkan dengan pengetahuan yang benar-benar dipakai saat run tersebut. |
| Recipe evaluasi | Identitas protokol yang menentukan metrik dan cara pengukurannya. | Pergantian recipe dapat mengubah makna skor meskipun pertanyaannya sama. |

Ukuran chunk adalah pengaturan pemecahan teks, bukan jaminan bahwa setiap potongan selalu memiliki panjang yang persis sama. Pemisah bagian, judul, dan panjang isi ikut memengaruhi hasilnya. Metadata menyertakan keterangan seperti sumber atau bagian dokumen; metadata membantu pelacakan, tetapi nama berkas yang sesuai belum membuktikan bahwa isi passage menjawab pertanyaan.

## Hubungan chatbot dengan DeepEval

DeepEval adalah **library evaluasi**. Ia menyediakan kelas metrik, menyusun permintaan penilaian, memproses keluaran judge, dan menghasilkan skor. DeepEval bukan nama model penilai.

Pada contoh gambar:

| Komponen | Peran |
| --- | --- |
| `openai/gpt-6-luna` | Model yang menghasilkan jawaban chatbot pada run tersebut. |
| `deepseek/deepseek-v4.1-flash` | Model judge yang menilai hasil pada run tersebut. |
| OpenRouter | Jalur akses model yang digunakan project. |
| DeepEval | Library yang mengatur mekanisme metrik dan perhitungannya. |

Nama model pada gambar merupakan konfigurasi run itu, sehingga tidak perlu dianggap selalu sama untuk semua run berikutnya.

Alur untuk satu pertanyaan adalah sebagai berikut:

1. Sistem membaca pertanyaan dan jawaban acuan dari dataset.
2. Pipeline RAG mencari passage dan menghasilkan jawaban.
3. Project membentuk `LLMTestCase` untuk DeepEval.
4. DeepEval meminta judge memeriksa item sesuai metriknya.
5. Library menghitung atau menormalisasi hasil penilaian.
6. Project menyimpan skor per kasus dan menghitung rata-rata untuk dashboard.

Empat field utama pada satu kasus adalah:

```text
input              = pertanyaan pengguna
actual_output      = jawaban chatbot
expected_output    = jawaban acuan
retrieval_context  = daftar teks hasil retrieval
```

Setiap metrik menggunakan bagian yang berbeda dari kasus tersebut. Answer Relevancy berpusat pada pertanyaan dan jawaban, sedangkan Contextual Recall membutuhkan acuan serta konteks. Tidak semua metrik menghitung kemiripan antara dua jawaban.

Implementasinya dapat ditelusuri pada [`runner.py`](../../testing/evals/runner.py), [`durable.py`](../../testing/evals/durable.py), dan [`metrics.py`](../../testing/evals/metrics.py). Menjalankan satu metrik dapat melibatkan beberapa panggilan model, misalnya untuk mengekstrak klaim, memberi verdict, dan menulis alasan. Sepuluh kasus dengan lima metrik berarti 50 penilaian kasus–metrik, bukan otomatis 50 request API.

## Bagian mana yang matematis dan bagian mana yang menggunakan LLM

Untuk empat metrik pertama pada gambar, pembagiannya umumnya seperti ini:

```text
LLM menentukan item dan verdict → kode menghitung rasio atau bobot → skor
```

Sebagai contoh, pembagian `3/4` dapat dihitung ulang dengan pasti. Akan tetapi, keputusan bahwa ada empat klaim dan tiga di antaranya diterima berasal dari judge. Karena itu, adanya rumus tidak membuat keseluruhan pengukuran menjadi bebas dari penilaian LLM.

G-Eval memakai mekanisme penilaian rubrik. Skornya tidak diperoleh dengan menghitung jumlah jawaban benar dibagi seluruh jawaban.

Pembahasan berikut mengacu pada jalur **LLM-as-a-judge**. Project mematok DeepEval `4.2.8`; dokumentasi daring dapat berkembang dan menjelaskan mode lain. Untuk mereproduksi hasil, gunakan versi, mode, dan konfigurasi metrik yang tercatat pada run.

## Faithfulness

### Apa yang diperiksa

Faithfulness memeriksa keselarasan klaim jawaban dengan informasi pada konteks retrieval. Jawaban yang mengubah harga dari Rp20.000 dalam konteks menjadi Rp30.000 mengandung pertentangan yang dapat menurunkan skor. Dasar pemeriksaannya adalah konteks yang diberikan, sehingga pengetahuan sumber yang kedaluwarsa tetap dapat menghasilkan jawaban dengan skor tinggi. [Dokumentasi Faithfulness](https://deepeval.com/docs/metrics-faithfulness).

Pada konfigurasi project yang diperiksa, verdict `yes` dan `borderline` ikut diterima. `borderline` adalah kategori ambigu; ia tidak sama dengan dukungan faktual yang tegas. Perilaku ini tercermin dalam fungsi `judge_calculation()` di [`calculations.py`](../../testing/evals/calculations.py).

### Rumus pada konfigurasi tersebut

$$
F = \frac{N_{yes} + N_{borderline}}{N_{verdict}}
$$

`N_verdict` adalah jumlah verdict valid yang dinilai. Jika `penalize_ambiguous_claims` diaktifkan, perlakuan terhadap klaim ambigu berubah; jangan memakai rumus konfigurasi ini tanpa memeriksa pengaturannya.

### Contoh hitung

| Klaim | Verdict | Dihitung sebagai diterima |
| --- | --- | --- |
| A | `yes` | 1 |
| B | `yes` | 1 |
| C | `borderline` | 1 |
| D | `no` | 0 |

```text
F = (2 + 1) / 4 = 0,75 = 75%
```

Skor tersebut berarti 75% verdict diterima menurut kebijakan metrik. Ia tidak membuktikan bahwa 75% klaim telah diverifikasi secara tegas oleh staf. Untuk contoh ini, hanya dua verdict yang berupa `yes`.

## Answer Relevancy

### Apa yang diperiksa

Answer Relevancy menilai apakah pernyataan dalam jawaban berkaitan dengan pertanyaan. Jawaban harga yang membahas luas dan biaya cetak dapat relevan, sedangkan tambahan cerita tentang olahraga tidak membantu menjawab pertanyaan itu. Relevansi tetap berbeda dari kebenaran: jawaban dapat membahas harga yang diminta, tetapi menyebut nominal yang salah. [Dokumentasi Answer Relevancy](https://deepeval.com/docs/metrics-answer-relevancy).

### Rumus

Pada konfigurasi project, `yes` dan `borderline` diterima:

$$
AR = \frac{N_{pernyataan\ diterima}}{N_{pernyataan\ dinilai}}
$$

### Contoh hitung

Judge memisahkan jawaban menjadi empat pernyataan, lalu menerima tiga sebagai relevan:

```text
AR = 3 / 4 = 0,75 = 75%
```

Jumlah pernyataan mengikuti hasil ekstraksi dan verdict judge. Skor tinggi perlu dibaca bersama Faithfulness dan pemeriksaan bisnis, terutama untuk pertanyaan yang melibatkan angka.

## Contextual Recall

### Apa yang diperiksa

Contextual Recall memeriksa apakah pernyataan dalam **jawaban acuan** dapat didukung oleh konteks yang ditemukan. Fokusnya adalah kelengkapan bukti untuk menjawab pertanyaan ideal, bukan jumlah klaim dalam jawaban aktual. Judge menilai keterlacakan pernyataan acuan, lalu library menghitung proporsinya. [Dokumentasi Contextual Recall](https://deepeval.com/docs/metrics-contextual-recall).

### Rumus

$$
CR = \frac{N_{pernyataan\ acuan\ yang\ didukung}}{N_{seluruh\ pernyataan\ acuan}}
$$

### Contoh hitung

Jawaban acuan membutuhkan tiga informasi:

| Informasi acuan | Ditemukan dalam konteks menurut judge |
| --- | --- |
| Jenis bahan | Ya |
| Harga per satuan | Ya |
| Ketentuan pembayaran | Tidak |

```text
CR = 2 / 3 ≈ 0,6667 ≈ 66,67%
```

Contoh ini memakai seluruh konteks yang dikirim ke penilaian. Jika ada lima passage, dukungan boleh ditemukan pada passage kelima. Contextual Recall tidak memberi bobot peringkat seperti Contextual Precision.

Angka `66,67%` di sini bukan berarti dua dari tiga dokumen ditemukan. Unitnya adalah pernyataan acuan. Acuan yang salah atau terlalu luas juga dapat menurunkan skor, sehingga penulis perlu memeriksa sumber sebelum menyimpulkan bahwa masalahnya selalu berada pada retriever.

## Contextual Precision

### Apa yang diperiksa

Contextual Precision menilai penempatan passage relevan dalam urutan hasil retrieval. Judge menentukan relevansi passage terhadap pertanyaan dengan mempertimbangkan jawaban acuan. Kode kemudian menggunakan **weighted cumulative precision**. Perhitungan ini berbeda dari pembagian sederhana jumlah passage relevan dengan `k`. [Dokumentasi Contextual Precision](https://deepeval.com/docs/metrics-contextual-precision).

### Rumus

Misalkan `r_i = 1` jika passage pada rank ke-i dinilai relevan, dan `0` jika tidak. Precision pada suatu peringkat adalah:

$$
P@i = \frac{\sum_{j=1}^{i} r_j}{i}
$$

Contextual Precision dihitung sebagai:

$$
CP = \frac{\sum_{i=1}^{k} (P@i \times r_i)}{\sum_{i=1}^{k} r_i}
$$

Penyebutnya adalah jumlah passage yang dinilai relevan dalam hasil yang diperiksa. Pada implementasi DeepEval yang diperiksa, jika tidak ada passage relevan, skor dikembalikan sebagai 0; tidak dilakukan pembagian dengan nol.

### Contoh hitung

Lima passage memperoleh label `[1, 0, 1, 0, 1]`:

| Rank | Relevan `r_i` | `P@i` | Kontribusi `P@i × r_i` |
| --- | --- | --- | --- |
| 1 | 1 | 1/1 | 1 |
| 2 | 0 | 1/2 | 0 |
| 3 | 1 | 2/3 | 2/3 |
| 4 | 0 | 2/4 | 0 |
| 5 | 1 | 3/5 | 3/5 |

```text
CP = (1 + 2/3 + 3/5) / 3
   ≈ 0,7556
   ≈ 75,56%
```

Bandingkan dua susunan berikut:

| Label relevansi lima passage | Precision@5 sederhana | Contextual Precision |
| --- | --- | --- |
| `[1, 0, 0, 0, 0]` | 1/5 = 20% | 1/1 = 100% |
| `[0, 0, 0, 0, 1]` | 1/5 = 20% | (1/5)/1 = 20% |

Jumlah passage relevannya sama, tetapi susunan pertama menempatkan passage tersebut di awal. Skor CP 100% pada susunan pertama tidak membuktikan bahwa semua passage relevan atau seluruh fakta acuan sudah tercakup.

## Business correctness melalui G-Eval

### Apa yang diperiksa

`Business correctness` merupakan **nama metrik kustom project**, sedangkan G-Eval adalah mekanisme penilaiannya. Kriteria pada [`metrics.py`](../../testing/evals/metrics.py) meminta judge membandingkan jawaban dengan acuan dan pengetahuan usaha. Harga, satuan, jumlah, ketentuan, serta perhitungan harus tepat. Kriteria juga mengutamakan klarifikasi yang sesuai daripada mengarang spesifikasi yang belum diberikan.

Project menyertakan pertanyaan, jawaban aktual, jawaban acuan, dan konteks sebagai parameter penilaian. Catatan kasus yang telah direview dapat melengkapi kriterianya. Ini merupakan penilaian otomatis; hasilnya berbeda dari lembar penilaian staf.

### Cara kerja dan perhitungan

Jika hanya `criteria` diberikan, G-Eval dapat menghasilkan langkah evaluasi sebelum memberi nilai. Pada konfigurasi tanpa rubrik rentang khusus seperti di sini, rentang dasar adalah 0 sampai 10 dan hasil dinormalisasi menjadi 0 sampai 1. Jalur yang mendukung log-probability dapat memperhalus nilai dengan pembobotan kandidat skor. Jalur tanpa dukungan tersebut dapat memakai skor mentah. [Dokumentasi G-Eval](https://deepeval.com/docs/metrics-llm-evals).

Untuk skor mentah `s` pada rentang dasar tersebut:

$$
G = \frac{s}{10}
$$

Contoh ilustratif: skor rubrik `8` menghasilkan `8/10 = 0,80`. Ini bukan hasil menghitung delapan fakta benar dari sepuluh fakta.

Untuk memahami pembobotan probabilitas secara sederhana, misalkan `q_s` adalah bobot probabilitas kandidat skor yang telah dinormalisasi:

$$
G = \frac{\sum_s q_s \times s}{10}
$$

```text
Kandidat skor 7 memiliki bobot 0,25
Kandidat skor 8 memiliki bobot 0,75

Skor berbobot = (0,25 × 7) + (0,75 × 8) = 7,75
G = 7,75 / 10 = 0,775 = 77,50%
```

Ini ilustrasi prinsip pembobotan, bukan rekonstruksi nilai pada gambar. Angka agregat saja tidak membuktikan jalur mana yang dipakai pada sebuah run. Periksa respons dan bukti perhitungan yang tersimpan bila memerlukan penjelasan sampai tingkat tersebut.

G-Eval tetap bergantung pada kriteria, acuan, dan judge. Nilai tinggi tidak menggantikan pemeriksaan manusia untuk kebijakan usaha atau perhitungan yang berdampak pada pelanggan.

## Membaca angka pada dashboard

### Persentase adalah rata-rata skor kasus

Untuk metrik `m`, misalkan `s_i,m` adalah skor suatu kasus dan `n_m` adalah jumlah kasus yang memiliki skor tersedia:

$$
\operatorname{Mean}(m) = \frac{\sum_{i \in V_m} s_{i,m}}{n_m}
$$

`V_m` adalah kumpulan kasus dengan skor valid yang tersedia. Nilai tampilan persen adalah rata-rata tersebut dikalikan 100.

Contoh lima kasus, dengan satu skor tidak tersedia:

```text
Skor tersedia = 0,80; 0,70; 0,90; 0,60
Satu kasus lain = tidak tersedia

Rata-rata = (0,80 + 0,70 + 0,90 + 0,60) / 4
          = 0,75
Tampilan  = 75%
Jumlah    = 4/5 case scores
```

Skor yang hilang tidak diubah menjadi 0. Sebaliknya, skor rendah yang sah tetap ikut dihitung. Masing-masing metrik dapat memiliki jumlah skor tersedia yang berbeda.

Penghitungan ini merupakan rata-rata per kasus. Untuk metrik berbasis klaim, ia berbeda dari mengumpulkan seluruh klaim lintas kasus lalu menghitung satu rasio besar. Dalam rata-rata per kasus, pertanyaan dengan dua klaim dan pertanyaan dengan sepuluh klaim tetap memiliki bobot kasus yang sama.

Implementasi agregasi terdapat pada [`durable.py`](../../testing/evals/durable.py), sedangkan penjelasan pembaginya ditampilkan oleh [`evaluation-math.tsx`](../../frontend/src/components/evaluation-math.tsx).

### Arti angka pada gambar

| Tampilan | Cara membaca |
| --- | --- |
| Faithfulness 93% | Rata-rata skor keselarasan klaim dengan konteks, setelah pembulatan tampilan. |
| Answer Relevancy 99% | Rata-rata skor relevansi pernyataan jawaban terhadap pertanyaan. |
| Contextual Recall 72% | Rata-rata skor dukungan konteks terhadap pernyataan acuan. |
| Contextual Precision 73% | Rata-rata skor susunan konteks relevan menurut perhitungan berbobot peringkat. |
| Business correctness 75% | Rata-rata skor rubrik bisnis dari G-Eval. |
| `10/10 case scores` | Semua sepuluh kasus memiliki skor untuk metrik tersebut; bukan berarti semua kasus lulus. |

Nilai 75% G-Eval tidak berarti tepat 75% jawaban atau transaksi bisnis benar. Demikian pula, Contextual Recall 72% tidak berarti tepat 72% dokumen berhasil ditemukan. Gunakan nilai asli yang belum dibulatkan ketika menghitung ulang rata-rata.

### Skor berbeda dari status lulus

Metrik judge pada project menggunakan ambang `0,70`. Sebuah kasus dapat dinyatakan memenuhi ambang ketika skornya mencapai batas tersebut. Rata-rata skor dan proporsi kasus yang memenuhi ambang merupakan dua penghitungan berbeda.

Ambang ini adalah pengaturan evaluasi pada sistem, bukan standar universal bahwa semua chatbot dengan skor 70% sudah layak. Menurunkan ambang juga tidak meningkatkan kualitas jawaban.

## Mengapa antarmetrik bisa terlihat bertentangan

| Pola hasil | Penjelasan yang perlu diperiksa | Tindak lanjut |
| --- | --- | --- |
| Faithfulness tinggi, Contextual Recall rendah | Jawaban mengikuti konteks yang tersedia, tetapi konteks belum mencakup seluruh kebutuhan acuan. | Periksa passage yang hilang dan ketepatan acuan. |
| Answer Relevancy tinggi, Business correctness rendah | Jawaban membahas kebutuhan pengguna, tetapi harga, satuan, atau perhitungannya bermasalah. | Periksa ketentuan usaha dan angka secara langsung. |
| Contextual Recall tinggi, Contextual Precision rendah | Informasi yang diperlukan tersedia, tetapi passage relevan mungkin muncul terlambat. | Baca urutan dan label relevansi passage. |
| Contextual Precision tinggi, Contextual Recall rendah | Passage yang dinilai relevan muncul di awal, tetapi sebagian fakta acuan belum terambil. | Periksa kelengkapan isi; jangan menyimpulkan dari peringkat saja. |

Pola tersebut membantu diagnosis, bukan bukti penyebab tunggal. Misalnya, memperbesar `k` dapat menambah informasi sekaligus menambah konteks yang tidak membantu.

## Batas penilaian otomatis

- Judge dapat salah memisahkan klaim, memberikan verdict, atau menulis alasan. Cocokkan kembali dengan pertanyaan, acuan, jawaban, dan konteks.
- Ground truth merupakan acuan evaluasi yang harus benar; nama field tersebut tidak menjamin isi selalu benar atau mutakhir.
- `temperature=0` pada judge membantu mengendalikan variasi, tetapi tidak menjamin semua penilaian identik pada setiap pemanggilan.
- Ketika Faithfulness atau Answer Relevancy tidak menghasilkan item untuk dinilai, versi dan konfigurasi yang diperiksa mengembalikan 1 sebagai konvensi library. Ini bukan bukti jawaban kosong merupakan jawaban yang benar. Pada Contextual Recall, daftar verdict kosong menghasilkan 0.
- Persentase saja tidak cukup untuk merekonstruksi pembilang dan penyebut. Skor 75% tidak otomatis berasal dari tiga item diterima dari empat item.

Project menyimpan jejak `calculation` hanya jika perhitungannya cocok dengan skor aktual. Jejak ini dapat memuat pembilang, penyebut, item yang dihitung, serta verdict. Jika hasil historis tidak memiliki jejak tersebut, gunakan alasan penilaian dan artefak kasus yang tersedia tanpa mengarang jumlah item. Lihat [`judge_calculation()`](../../testing/evals/calculations.py) dan [panduan metode evaluasi](../evaluation-methodology.md).

## Perubahan protokol pada project ini

Kode membedakan recipe QA baru `rag-four-metrics-v1` dari protokol historis:

| Protokol | Metrik yang dilaporkan |
| --- | --- |
| Hasil historis pada gambar | Faithfulness, Answer Relevancy, Contextual Recall, Contextual Precision, dan Business correctness [GEval]. |
| QA baru (`rag-four-metrics-v1`) | Faithfulness, Answer Relevancy, Contextual Recall, dan Contextual Precision; keempatnya memakai LLM judge. |
| Recipe anotasi historis (`chunking-fact-coverage-v1`) | Faithfulness, Answer Relevancy, Precision@k, dan Fact Coverage@k; dipertahankan untuk melanjutkan checkpoint lama. |

Pada QA baru, Contextual Recall dan Contextual Precision memakai jawaban acuan serta konteks retrieval; anotasi offline tidak diperlukan. Pada recipe anotasi historis, dua ukuran retrieval berikut dihitung dari label yang sesuai dengan pertanyaan dan snapshot passage:

$$
Precision@k = \frac{N_{passage\ relevan\ yang\ dikembalikan}}{k_{diminta}}
$$

$$
Fact\ Coverage@k = \frac{N_{fakta\ acuan\ unik\ yang\ tercakup}}{N_{seluruh\ fakta\ acuan}}
$$

Misalnya, dari lima passage yang diminta, tiga diberi anotasi relevan: Precision@5 = `3/5 = 60%`. Jika passage tersebut secara keseluruhan mencakup tiga dari empat fakta acuan, Fact Coverage@5 = `3/4 = 75%`. Fakta yang berulang karena overlap hanya dihitung sekali. Apabila hanya tiga passage dikembalikan untuk permintaan `k=5`, penyebut Precision tetap 5 pada implementasi ini.

Pembagian kode tersebut deterministik setelah label ditetapkan. Kualitas label tetap memerlukan pemeriksaan. Nama berkas yang sesuai tidak otomatis menjadi label relevansi isi.

Jika anotasi belum tersedia atau tidak cocok dengan snapshot, hasilnya **unavailable**, bukan nol. Pergantian chunking mengubah passage, sehingga label pendukungnya perlu diperiksa dan disesuaikan kembali. Setelah anotasi dinyatakan cocok, kasus tanpa passage hasil retrieval menghasilkan nol sesuai aturan implementasi.

Fact Coverage@k merupakan ukuran operasional yang didefinisikan project ini. Ia tidak sama dengan Contextual Recall DeepEval maupun recall standar atas seluruh dokumen relevan. Contextual Precision historis juga tidak boleh sekadar diberi nama baru Precision@k.

Penilaian staf internal dan SUS WhatsApp tetap merupakan instrumen penelitian tersendiri. Keduanya tidak dihitung sebagai Business correctness G-Eval atau digabungkan ke rata-rata metrik QA baru. Protokol percakapan multi-turn memiliki metrik tersendiri dan berada di luar lima metrik single-turn dalam panduan ini.

## Menggunakan metrik untuk membandingkan chunking

Perbandingan yang dapat ditafsirkan memerlukan pengaturan pembanding yang terkontrol:

1. Gunakan pertanyaan dan fakta acuan yang sama serta sudah diperiksa.
2. Pertahankan korpus, embedding, `k`, prompt, dan model jawaban ketika fokusnya menguji chunking.
3. Pertahankan judge, versi DeepEval, mode, kriteria, dan recipe evaluasi.
4. Ubah konfigurasi chunking yang sedang diuji, lalu catat snapshot hasilnya. Untuk ukuran berbasis anotasi, sesuaikan label terhadap passage pada snapshot tersebut.
5. Baca skor tiap kasus beserta konteksnya, bukan hanya persentase rata-rata.
6. Ulangi pengukuran bila hendak menilai kestabilan, dan pisahkan pertanyaan pengembangan dari pertanyaan baru untuk pemeriksaan akhir.

Jika model, korpus, dan chunking berubah sekaligus, kenaikan skor tidak dapat dijelaskan sebagai pengaruh chunking saja. Jika definisi metrik atau acuan berubah, buat pembanding yang dinilai dengan protokol yang sama.

## Rujukan kode dan bacaan lanjutan

| Berkas | Bagian yang dapat dipelajari |
| --- | --- |
| [`testing/evals/metrics.py`](../../testing/evals/metrics.py) | Pemilihan metrik, model judge, ambang, dan kriteria Business correctness. |
| [`testing/evals/runner.py`](../../testing/evals/runner.py) | Pembentukan kasus, pemanggilan `metric.measure()`, penyimpanan skor, dan agregasi. |
| [`testing/evals/durable.py`](../../testing/evals/durable.py) | Pelaksanaan bertahap dan pemeliharaan recipe ketika pekerjaan dilanjutkan. |
| [`testing/evals/calculations.py`](../../testing/evals/calculations.py) | Perhitungan retrieval berbasis anotasi dan jejak perhitungan verdict judge. |
| [`frontend/src/components/evaluation-math.tsx`](../../frontend/src/components/evaluation-math.tsx) | Penjelasan rumus, skor tersedia, dan keterbatasan jejak historis pada UI. |
| [`docs/evaluation-methodology.md`](../evaluation-methodology.md) | Aturan empat metrik QA dan interpretasi anotasi historis. |
| [`app/admin/chunking.py`](../../app/admin/chunking.py) | Pengaturan pemecahan teks berbasis karakter. |

Dokumentasi resmi metrik: [Faithfulness](https://deepeval.com/docs/metrics-faithfulness), [Answer Relevancy](https://deepeval.com/docs/metrics-answer-relevancy), [Contextual Recall](https://deepeval.com/docs/metrics-contextual-recall), [Contextual Precision](https://deepeval.com/docs/metrics-contextual-precision), dan [G-Eval](https://deepeval.com/docs/metrics-llm-evals).

Panduan diselaraskan dengan perubahan setelah checkout `fc629f4` dan DeepEval terpasang `4.2.8` pada 20 Oktober 2026. Penyusunan panduan tidak menjalankan evaluasi model baru.
