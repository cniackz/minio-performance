# MinIO Version Benchmarking

This project automates performance benchmarking of **multiple MinIO versions** using [`warp`](https://github.com/minio/warp).

It runs each version in sequence, measures throughput, and records results into a CSV file.

## How It Works

```
 ┌─────────────────────┐
 │ discover versions   │
 │  in ~/minio_versions│
 └──────────┬──────────┘
            │
   for each version:
            │
   ┌────────▼───────────┐
   │ kill existing      │
   │ MinIO processes    │
   └────────┬───────────┘
            │
   ┌────────▼───────────┐
   │ clean /Volumes/    │
   │ data1..4 dirs      │
   └────────┬───────────┘
            │
   ┌────────▼───────────┐
   │ start MinIO (fg)   │
   │ execute_minio.py   │
   └────────┬───────────┘
            │ wait until
            │ port 9000 open
            │
   ┌────────▼───────────┐
   │ run warp           │
   │ execute_warp.py    │
   └────────┬───────────┘
            │ parse "Average:"
            │
   ┌────────▼───────────┐
   │ append to CSV      │
   └────────┬───────────┘
            │
   ┌────────▼───────────┐
   │ stop MinIO         │
   └────────────────────┘
```

## Scripts

* **`execute_minio.py`** – Starts a specific MinIO binary from a given version folder, optionally cleaning volumes first.
* **`bench_all_versions.py`** – Loops over all discovered versions and runs the benchmark sequence.
* **`execute_warp.py`** – Runs a `warp` workload against the currently running MinIO instance.

## Requirements

* Python 3.8+
* MinIO server binaries in `~/minio_versions/`:

  ```
  ~/minio_versions/
    ├─ RELEASE.2025-08-11T04-07-05Z/minio
    ├─ RELEASE.2025-08-07T19-14-57Z/minio
    └─ ...
  ```
* `warp` binary in your PATH.
* Local volumes mounted at `/Volumes/data1` … `/Volumes/data4`.

## Usage

1. Place MinIO versions in `~/minio_versions` as described above.
2. Make sure `/Volumes/data1`–`data4` exist and are writable.
3. Run:

```bash
python3 bench_all_versions.py
```

4. Results will be saved in `versions_speeds.csv`:

```csv
version,MiBps
RELEASE.2025-08-11T04-07-05Z,492.35
RELEASE.2025-08-07T19-14-57Z,488.12
...
```

## Customization

* Adjust `BASE` in `bench_all_versions.py` to change where MinIO versions are stored.
* Adjust `DEFAULT_MINIO_ARGS` in `execute_minio.py` to modify how MinIO is launched.
* Update `EXEC_WARP` to point to your warp execution script.

