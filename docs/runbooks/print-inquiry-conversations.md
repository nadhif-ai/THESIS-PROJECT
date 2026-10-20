# Ringkasan kebutuhan cetak dan pilihan cabang

Tujuan percakapan adalah membantu pelanggan menyiapkan kebutuhan cetak untuk dikonfirmasi toko. Ringkasan kebutuhan bukan booking resmi, konfirmasi harga, atau tanda pesanan masuk antrean produksi.

## Perilaku yang diharapkan

1. Sapaan pertama menampilkan pengenalan dan empat kategori informasi. Sapaan di tengah percakapan cukup singkat. `menu` menampilkan kategori kembali.
2. Saat pelanggan ingin memesan atau menyetujui tawaran rangkuman, bot merangkum spesifikasi terbaru. Detail yang belum diputuskan ditandai perlu konfirmasi. Rekomendasi bahan dibedakan dari pilihan pelanggan.
3. Harga hanya boleh berasal dari knowledge aktif. Estimasi yang sudah dikoreksi tidak menjadi total yang disetujui. Harga yang belum tersedia tidak menghalangi rangkuman.
4. Bot menanyakan cabang pilihan dengan nama dari knowledge aktif. Jika cabang sudah disebutkan, bot langsung memberikan langkah berikutnya. Permintaan lokasi terdekat memerlukan area pelanggan.
5. Setelah cabang dipilih, bot memberikan alamat, Maps, dan patokan yang tersedia dalam konteks. Pelanggan membawa ringkasan serta file desain ke toko, atau menghubungi admin melalui jalur pemesanan yang tersedia dalam knowledge. Nomor admin umum tidak boleh dianggap nomor khusus cabang tanpa sumber yang menjelaskannya.
6. Admin toko mengonfirmasi file, harga, dan jadwal pengerjaan. Bot tidak mengklaim sudah meneruskan permintaan, menerima pembayaran, atau memasukkan pesanan ke antrean.

Angka 1 sampai 4 menjadi pilihan kategori saat awal percakapan atau sesudah menu. Pada percakapan aktif, angka mengikuti pertanyaan terakhir, misalnya jumlah produk atau pilihan cabang. Ketik `menu` jika ingin kembali ke kategori.

`reset` memulai konteks baru dan menampilkan orientasi awal lagi. Audit percakapan tetap tersimpan. Kata `batal` tidak lagi menjadi alias reset karena dapat berarti pembatalan pesanan; bot mengarahkan pengecekan pembatalan ke admin.

## Pengaturan dan rilis

- Sapaan dan routing persetujuan berada di `app/backend/chain.py`.
- Aturan ringkasan dan batas kewenangan berada di aturan inti `app/backend/prompt_template.py`. Aturan berlaku juga pada prompt percakapan kustom yang sudah tersimpan, tanpa menimpa prompt tersebut. Fingerprint prompt mencakup aturan inti.
- Pencarian lanjutan memperkaya pertanyaan yang terkait cabang atau kelanjutan pemesanan dengan istilah lokasi dan kontak admin. Semua fakta bisnis tetap berasal dari hasil retrieval pada snapshot aktif; alamat dan nomor tidak disalin ke kode.
- Perubahan kode memerlukan restart backend lokal atau deployment baru. Tidak memerlukan reindex untuk aturan percakapan. Perubahan sumber alamat/kontak tetap mengikuti proses **Sync knowledge**.

## Verifikasi lokal

Jalankan disposable PostgreSQL sesuai `AGENTS.md`, lalu:

```sh
LANGSMITH_TRACING=false venv/bin/python -m pytest testing/test_print_inquiry.py testing/test_prompt_settings.py testing/test_rag_reliability.py -q
```

Tes offline memeriksa routing, riwayat, reset, retrieval query, dan aturan yang diterima model menggunakan provider tiruan. Tes tersebut belum membuktikan kualitas jawaban model nyata atau pengiriman WhatsApp produksi. Evaluasi berbayar mengikuti opt-in dan konfigurasi suite DeepEval yang sudah ada.

Verifikasi 20 Oktober 2026: suite offline lengkap (`LANGSMITH_TRACING=false venv/bin/python -m pytest -q`) menghasilkan 224 passed dan 11 skipped. Evaluasi berbayar tidak dijalankan. Perubahan belum dideploy dan belum diuji melalui WhatsApp produksi.

## Skenario penerimaan di Playground atau WhatsApp

| Percakapan | Yang diperiksa |
| --- | --- |
| `hey`, lalu `halo` | Orientasi lengkap pertama, sapaan singkat berikutnya. |
| Spesifikasi stiker 10 × 10 cm, 50 pcs; harga sebelumnya dikoreksi; `oke sip gw approve mau pesen itu ya` | Ringkasan mempertahankan spesifikasi, tidak mengulang total yang dikoreksi, menanyakan cabang. |
| Menyetujui tawaran rangkuman dengan `oke` | Bot melanjutkan rangkuman, bukan sekadar mengirim “Siap”. |
| Memilih nama cabang yang ditawarkan | Alamat/Maps berasal dari konteks aktif; bot tidak bertanya cabang yang sama lagi. |
| Menjawab `2` setelah bot menawarkan cabang bernomor | Bot menafsirkan cabang, bukan membuka kategori persiapan file. |
| Menjawab `2` setelah `menu` | Contoh pertanyaan persiapan file tampil. |
| `Yang paling dekat aja` tanpa area asal | Bot meminta area pelanggan, tidak mengaku mengetahui lokasi. |
| `Makasih` atau `oke` untuk mengakhiri penjelasan | Penutup singkat tanpa dorongan memesan atau rangkuman berulang. |
| Knowledge tidak memuat alamat, Maps, atau kontak tertentu | Bot menjelaskan informasi yang perlu konfirmasi tanpa membuat tautan pengganti. |
| `Pesanan saya kemarin mau dibatalkan`, lalu `batal` | Bot mengarahkan pengecekan ke admin, tidak menghapus konteks atau mengaku membatalkan pesanan. |
| `reset` | Konteks dimulai kembali; riwayat audit tetap ada. |
