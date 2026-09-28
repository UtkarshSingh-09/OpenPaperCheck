"""
Benchmark local SQLite snapshot lookup performance on 50,000 records.
Verifies whether keyed DOI lookups execute in < 2.0 ms.
"""

import random
import sqlite3
import time
from pathlib import Path

from openpapercheck.core.storage import get_retraction, init_schema


def run_benchmark(records_count: int = 50000, queries_count: int = 1000):
    db_path = Path("/tmp/bench_retractions.sqlite")
    if db_path.is_file():
        db_path.unlink()

    print(f"Creating benchmark database with {records_count:,} records at {db_path}...")
    conn = sqlite3.connect(db_path)
    init_schema(conn)
    c = conn.cursor()

    batch = []
    generated_dois = []
    for i in range(1, records_count + 1):
        doi = f"10.1000/bench.{i}.{random.randint(1000, 9999)}"
        generated_dois.append(doi)
        batch.append(
            (
                i,
                doi,
                f"{doi}.ret",
                "Retraction",
                "Falsification of Data; Plagiarism",
                "2023-01-01",
                "2020-01-01",
                "https://example.com/notice",
            )
        )
        if len(batch) >= 5000:
            c.executemany(
                """
                INSERT INTO retraction_records (
                    rw_record_id, original_doi, retraction_doi, nature,
                    reasons, retraction_date, original_date, notice_urls
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                batch,
            )
            batch = []

    if batch:
        c.executemany(
            """
            INSERT INTO retraction_records (
                rw_record_id, original_doi, retraction_doi, nature,
                reasons, retraction_date, original_date, notice_urls
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            batch,
        )
    conn.commit()
    conn.close()

    print(f"Inserted {records_count:,} records. Running {queries_count:,} random queries...")
    sample_queries = random.sample(generated_dois, queries_count)

    latencies_ms = []
    for doi in sample_queries:
        t0 = time.perf_counter()
        res = get_retraction(doi, db_path=db_path)
        t1 = time.perf_counter()
        assert res is not None
        latencies_ms.append((t1 - t0) * 1000.0)

    latencies_ms.sort()
    avg_latency = sum(latencies_ms) / len(latencies_ms)
    p50 = latencies_ms[int(len(latencies_ms) * 0.50)]
    p95 = latencies_ms[int(len(latencies_ms) * 0.95)]
    p99 = latencies_ms[int(len(latencies_ms) * 0.99)]

    print(f"--- Benchmark Results ({records_count:,} rows, {queries_count:,} lookups) ---")
    print(f"Average latency: {avg_latency:.4f} ms")
    print(f"p50 latency:     {p50:.4f} ms")
    print(f"p95 latency:     {p95:.4f} ms")
    print(f"p99 latency:     {p99:.4f} ms")

    if db_path.is_file():
        db_path.unlink()

    assert p95 < 2.0, f"Expected p95 latency < 2.0 ms, got {p95:.2f} ms"
    print("✓ Success: Verified sub-2ms query performance!")


if __name__ == "__main__":
    run_benchmark()
