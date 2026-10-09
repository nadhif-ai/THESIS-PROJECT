# Aturan Penulisan Naskah Skripsi & Gaya Bahasa Mahasiswa

Dokumen ini memuat panduan gaya bahasa, format penulisan, dan penyusunan kode program untuk naskah skripsi (khususnya BAB IV). Seluruh asisten (Gemini / Antigravity Agent) **wajib mematuhi aturan ini secara konsisten**.

---

## 1. Persona & Gaya Bahasa (Opsi A: Mengalir & Santai-Formal)
* **Sudut Pandang**: Ditulis dari sudut pandang mahasiswa yang menyusun laporan skripsi secara wajar, jelas, dan mudah dipahami baik oleh dosen pembimbing, penguji, maupun pembaca umum.
* **Kosakata Sederhana & Lugas**:
  * Hindari kosakata yang berbelit-belit, kaku berlebihan, atau istilah sastra/filsafat tinggi (misalnya: hindari kata *instansiasi tunggal*, *derajat keterkaitan*, *rasionalisasi komparatif*).
  * Gunakan kalimat yang mengalir dan wajar (misalnya: *koneksi database*, *menghemat memori*, *mencocokkan pertanyaan dengan dokumen*, *alur program*, *pengaturan sistem*).
  * Istilah teknis standar (*database*, *ChromaDB*, *embedding*, *cache*, *chunking*, *vectorstore*, *query*, *FastAPI*, *webhook*, *prompt*) tetap ditulis secara wajar tanpa dipaksakan ke terjemahan Indonesia yang membingungkan.

---

## 2. Struktur Penyusunan Kode (Teknik Sandwich & Breakdown)
Setiap kali menyajikan cuplikan kode program (*Listing Program*), gunakan formula **Teknik Sandwich**:

1. **Narasi Pengantar (Top Bun)**:
   * 1–2 kalimat pengantar yang menjelaskan tujuan dibuatnya fungsi atau potongan kode tersebut.
2. **Format Judul & Penomoran**:
   * Tuliskan nomor dan judul listing tepat di atas blok kode dengan penomoran berurutan (misal: `Listing 1`, `Listing 2`, `Listing 3`, dst.):
     `**Listing X: Judul Listing Singkat dan Jelas**`
3. **Potongan Kode Fokus (Patty - 5 s.d. 12 Baris Saja)**:
   * **Dilarang keras** menempelkan seluruh isi berkas program secara panjang sekaligus.
   * Kode wajib dipecah (*breakdown*) menjadi potongan kecil yang hanya berfokus pada 1 logika/fungsi spesifik.
4. **Narasi Penjelas / Bedah Logika (Bottom Bun)**:
   * 1 paragraf penjelasan di bawah kode yang menguraikan alur kerja kode dan kegunaan variabel penting dengan bahasa mengalir, sederhana, dan mudah dimengerti.

---

## 3. Contoh Pola yang Disepakati
```markdown
Fungsi `get_vectorstore()` digunakan untuk membuat koneksi ke database vektor ChromaDB, sebagaimana tercantum pada listing program berikut.

**Listing Program 4.6: Inisialisasi Database Vektor ChromaDB**
```python
def get_vectorstore() -> Chroma:
    global _chroma_instance
    if _chroma_instance is not None:
        return _chroma_instance
    settings = get_settings()
    _chroma_instance = Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=get_embedding_model(),
        persist_directory=settings.chroma_persist_dir,
        collection_metadata={"hnsw:space": "cosine"}
    )
    return _chroma_instance
```

Pada Listing Program 4.6 di atas, fungsi ini memeriksa apakah koneksi database sudah pernah dibuat sebelumnya lewat baris `_chroma_instance is not None`. Jika sudah ada, sistem langsung memakai koneksi tersebut tanpa harus membaca ulang berkas dari awal sehingga menghemat memori komputer. Pengaturan pencarian disetel menggunakan *cosine* agar sistem dapat mencocokkan pertanyaan pelanggan dengan informasi percetakan secara akurat.
```

---

## 4. Kecepatan & Alur Penyajian
* Sajikan isi naskah secara runtut sesuai urutan sub-bab dan nomor listing.
* Pertahankan format yang bersih, rapi, dan langsung siap disalin (*copy-paste*) ke lembar kerja Microsoft Word.
