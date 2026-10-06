"""
run_evaluation.py — Skrip Evaluasi Chatbot RAG CV. Asia Visual Grafika
Dibuat dari 0 untuk keperluan pengujian resmi Skripsi Bab V.

Metrik yang Diuji:
  AKURASI RETRIEVAL (ChromaDB Vectorstore):
   - Hit Rate@3  : Apakah dokumen acuan berhasil ditemukan di Top-3 hasil retrieval?
   - Precision@3 : Proporsi chunk yang relevan dari 3 chunk yang ditarik.

File Output:
   - testing/tabel_akurasi_retrieval.csv  (Tabel Akurasi Retrieval Bab V)
   - testing/ringkasan_evaluasi.txt       (Ringkasan Rata-rata Siap Copy ke Bab V)
"""

import sys
import csv
import datetime
from pathlib import Path

# Daftarkan root folder proyek agar modul app dapat diimpor
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.backend.vectorstore import similarity_search_with_score

# ---------------------------------------------------------------------------
# KONFIGURASI PENGUJIAN
# ---------------------------------------------------------------------------
TEST_DATASET  = Path(__file__).resolve().parent / "test_dataset.csv"
OUT_RETRIEVAL = Path(__file__).resolve().parent / "tabel_akurasi_retrieval.csv"
OUT_SUMMARY   = Path(__file__).resolve().parent / "ringkasan_evaluasi.txt"

TOP_K = 3


def load_test_dataset(filepath: Path) -> list[dict]:
    """Membaca pertanyaan uji dari file CSV dataset."""
    rows = []
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "id": r.get("id", "").strip(),
                "question": r.get("question", "").strip().strip('"'),
                "kategori_variasi": r.get("kategori_variasi", "").strip(),
                "expected_source": r.get("expected_source", "").strip(),
                "ground_truth": r.get("ground_truth", "").strip().strip('"'),
            })
    return rows


# ---------------------------------------------------------------------------
# EVALUASI AKURASI RETRIEVAL (TOP-3)
# ---------------------------------------------------------------------------
def run_retrieval_evaluation(dataset: list[dict]) -> dict:
    """
    Mengukur kemampuan ChromaDB menarik dokumen relevan pada Top-3.
    Menghasilkan: Hit Rate@3, Precision@3.
    """
    print("\n" + "=" * 70)
    print("  MENJALANKAN PENGUJIAN AKURASI RETRIEVAL (TOP-3)")
    print("=" * 70)

    retrieval_rows = []
    total_hit = 0
    total_precision = 0.0
    n = len(dataset)

    for idx, item in enumerate(dataset, 1):
        q = item["question"]
        expected = item["expected_source"]

        # Pencarian semantik Top-3 di ChromaDB
        raw_results = similarity_search_with_score(query=q, k=TOP_K)
        retrieved_docs = [doc for doc, _ in raw_results]
        retrieved_sources = [
            doc.metadata.get("source", "")
            for doc in retrieved_docs
            if doc.metadata.get("source")
        ]

        # Hitung hits (berapa chunk yang berasal dari dokumen acuan)
        hits = sum(1 for s in retrieved_sources if expected in s)

        hit_at_3 = 1 if hits > 0 else 0
        precision_at_3 = round(hits / TOP_K, 4)

        total_hit += hit_at_3
        total_precision += precision_at_3

        print(f"  [{idx:02d}/{n}] {q[:55]}...")
        print(f"         Hit@3: {hit_at_3} | Prec@3: {precision_at_3:.4f} | Sumber: {retrieved_sources}")

        retrieval_rows.append({
            "no": idx,
            "question": q,
            "kategori_variasi": item["kategori_variasi"],
            "expected_source": expected,
            "retrieved_sources": " | ".join(retrieved_sources),
            "hit@3": hit_at_3,
            "precision@3": precision_at_3,
        })

    avg_hit_rate = (total_hit / n) * 100
    avg_precision = total_precision / n

    # Simpan ke CSV
    fieldnames = ["no", "question", "kategori_variasi", "expected_source",
                  "retrieved_sources", "hit@3", "precision@3"]
    with open(OUT_RETRIEVAL, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(retrieval_rows)
        writer.writerow({
            "no": "Rata-rata",
            "question": "-",
            "kategori_variasi": "-",
            "expected_source": "-",
            "retrieved_sources": "-",
            "hit@3": f"{avg_hit_rate:.1f}%",
            "precision@3": f"{avg_precision:.4f}",
        })

    print(f"\n  >> Hasil Retrieval disimpan ke: {OUT_RETRIEVAL}")
    print(f"  >> Rata-rata: Hit Rate@3 = {avg_hit_rate:.1f}% | Precision@3 = {avg_precision:.4f}\n")

    return {
        "rows": retrieval_rows,
        "avg_hit_rate": avg_hit_rate,
        "avg_precision": avg_precision,
    }


# ---------------------------------------------------------------------------
# GENERASI RINGKASAN RESMI UNTUK BAB V
# ---------------------------------------------------------------------------
def generate_summary(retrieval_res: dict):
    now_str = datetime.datetime.now().strftime("%d %B %Y, %H:%M:%S")

    summary_lines = [
        "=" * 70,
        "  LAPORAN HASIL EVALUASI RESMI SKRIPSI (BAB V) — CV. ASIA VISUAL GRAFIKA",
        f"  Waktu Eksekusi : {now_str}",
        f"  Total Kueri    : 10 Pertanyaan Uji",
        "=" * 70,
        "",
        "TABEL HASIL PENGUJIAN AKURASI RETRIEVAL (TOP-3):",
        "-" * 70,
        f"  • Rata-rata Hit Rate@3    : {retrieval_res['avg_hit_rate']:.1f}%",
        f"  • Rata-rata Precision@3   : {retrieval_res['avg_precision']:.4f} ({retrieval_res['avg_precision']*100:.2f}%)",
        "-" * 70,
        "",
        "File Output Terkait:",
        f"  - Tabel Retrieval CSV : {OUT_RETRIEVAL}",
        "=" * 70,
    ]

    summary_text = "\n".join(summary_lines)
    with open(OUT_SUMMARY, "w", encoding="utf-8") as f:
        f.write(summary_text)

    print("\n" + summary_text)
    print(f"\n  [SUKSES] Ringkasan Bab V tersimpan di: {OUT_SUMMARY}\n")


# ---------------------------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------------------------
def main():
    if not TEST_DATASET.exists():
        print(f"[ERROR] File dataset {TEST_DATASET} tidak ditemukan!")
        sys.exit(1)

    print("Memuat dataset pengujian...")
    dataset = load_test_dataset(TEST_DATASET)
    print(f"Berhasil memuat {len(dataset)} pertanyaan uji.")

    # Jalankan pengujian Retrieval
    retrieval_res = run_retrieval_evaluation(dataset)

    # Buat ringkasan Bab V
    generate_summary(retrieval_res)


if __name__ == "__main__":
    main()
