#!/usr/bin/env python3
import subprocess
import time
import os
import csv
import re
from datetime import datetime
from pathlib import Path

# Configuración de credenciales para warp
os.environ["WARP_ACCESS_KEY"] = "minio"
os.environ["WARP_SECRET_KEY"] = "minio123"

# Dirección y puerto
warp_client_addr = "127.0.0.1:7761"
minio_host = "127.0.0.1:9000"

# Inicia warp client
client_proc = subprocess.Popen(
    ["warp", "client", warp_client_addr],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Espera unos segundos para que el cliente arranque
time.sleep(3)

AVG_RE = re.compile(r"^\s*\*\s*Average:\s*([\d.]+)\s*MiB/s", re.MULTILINE)  # <-- NUEVO

# Ejecuta la prueba de warp
try:
    run = subprocess.run([
        "warp", "put",
        "--warp-client", warp_client_addr,
        "--host", minio_host,
        "--bucket", "warp-test",
        "--duration", "20s",
        "--obj.size", "1MiB",
        "--concurrent", "32",
        "--noclear",
    ], check=True, text=True, capture_output=True)

    # Muestra la salida normal en consola como antes
    if run.stdout:
        print(run.stdout, end="")
    if run.stderr:
        print(run.stderr, end="")

    # Extrae el Average MiB/s y guarda CSV
    m = AVG_RE.search(run.stdout or "")
    if m:
        avg_mib = float(m.group(1))

        # Get MinIO Version
        version_file = Path("/tmp/minio_version.txt")
        if version_file.exists():
            minio_version = version_file.read_text().strip()
        else:
            minio_version = "UNKNOWN"

        row = [minio_version, avg_mib]

        with open("warp_results.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)
        print(f"\n✅ Guardado en warp_results.csv: {row}")
    else:
        print("\n⚠️ No se encontró la línea de 'Average' en la salida de warp.")

finally:
    # Mata el cliente al terminar la prueba
    client_proc.terminate()
    client_proc.wait()
