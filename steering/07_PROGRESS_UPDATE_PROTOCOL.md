# 07_PROGRESS_UPDATE_PROTOCOL.md — Protokol Auto-Update Progress

> 📌 **UNTUK APA FILE INI:** Aturan wajib Agent untuk selalu memperbarui `progress.md` dan `steering/02_THESIS_STATE.md` di setiap akhir sesi diskusi yang menghasilkan perubahan status atau keputusan baru.

---

## ATURAN WAJIB (PRIORITAS TINGGI)

### Kapan Agent WAJIB Update?

Agent **WAJIB** memperbarui `progress.md` di akhir sesi jika terjadi salah satu dari ini:

1. Ada sub-bab naskah yang statusnya berubah (kosong → ada draf, draf → selesai)
2. Ada data pengujian baru yang diperoleh (SUS, Human Eval, Black Box, Retrieval, Benchmark)
3. Ada keputusan baru terkait isi naskah atau metodologi
4. Ada teks naskah baru yang dihasilkan dan siap copy-paste ke Word
5. Ada blocker baru yang ditemukan atau blocker lama yang terselesaikan
6. Ada sesi diskusi yang menghasilkan output konkret apapun

### Apa yang HARUS Diupdate?

#### Di `progress.md`:
- Ubah status tabel audit (🔴 → 🟡 → 🟢) sesuai perkembangan nyata
- Tambahkan entri baru di bagian **LOG SESI DISKUSI** dengan format:

```
### Sesi [Tanggal]
- [Ringkasan output konkret sesi ini]
- [Perubahan status yang terjadi]
- [Tindak lanjut yang disepakati]
```

- Perbarui bagian **BLOCKER UTAMA** — hapus blocker yang sudah selesai, tambah blocker baru
- Perbarui **RENCANA AKSI PRIORITAS** jika ada pergeseran target hari

#### Di `steering/02_THESIS_STATE.md`:
- Perbarui status setiap bab di tabel Progres Penulisan Bab
- Perbarui status tabel Pengujian (kolom Status)
- Perbarui bagian Prioritas Aksi Hari Ini

---

## FORMAT LOG SESI DISKUSI (WAJIB DIISI SETIAP SESI)

```markdown
### Sesi [DD Bulan YYYY] — Hari ke-[X] dari 10
**Topik:** [Topik utama diskusi]
**Output Konkret:**
- [Daftar output nyata yang dihasilkan]
**Status Berubah:**
- [Nama sub-bab/pengujian]: [status lama] → [status baru]
**Tindak Lanjut:**
- [Apa yang harus dikerjakan Dif setelah sesi ini]
```

---

## CARA AGENT MENENTUKAN STATUS

| Simbol | Arti | Kriteria |
|--------|------|----------|
| 🔴 | Kosong / Belum dikerjakan | Belum ada konten sama sekali di Word |
| 🟡 | Ada sebagian / Draf awal | Ada isi tapi belum lengkap atau perlu revisi |
| 🟢 | Selesai / Siap bimbingan | Lengkap, sudah bisa dibawa ke dosen |
| 🔒 | Terkunci | Tidak boleh diubah lagi |

---

## CATATAN PENTING

- Jangan update `progress.md` di tengah diskusi — lakukan di **akhir sesi** setelah output konkret selesai.
- Jika sesi hanya berisi diskusi tanpa output nyata (tanya jawab teori, brainstorming), cukup catat di LOG SESI dengan output "Diskusi konsep [topik]".
- Format tanggal: DD Bulan YYYY (contoh: 1 Oktober 2026).
- Jangan hapus log lama — append saja di bawahnya.
- `progress.md` adalah dokumen milik Dif, bukan dokumen teknis — gunakan bahasa yang mudah dipahami.
