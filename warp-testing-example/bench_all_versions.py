#!/usr/bin/env python3
# bench_all_versions.py
import os, subprocess, time, socket, re, csv
from pathlib import Path

BASE = Path(os.path.expanduser("~/minio_versions"))
EXEC_MINIO = "/Users/cniackz/bash-config/execute_minio.py"
EXEC_WARP  = "/Users/cniackz/bash-config/execute_warp.py"
HOST = "127.0.0.1"
PORT = 9000
CSV_OUT = "versions_speeds.csv"

AVG_RE = re.compile(r"^\s*\*\s*Average:\s*([\d.]+)\s*MiB/s", re.MULTILINE)

# Ajusta aquí si quieres asegurar las credenciales del server
ENV = os.environ.copy()
ENV.setdefault("MINIO_ROOT_USER", "minio")
ENV.setdefault("MINIO_ROOT_PASSWORD", "minio123")
# Y del cliente warp (por si tu execute_warp no las fija)
ENV.setdefault("WARP_ACCESS_KEY", "minio")
ENV.setdefault("WARP_SECRET_KEY", "minio123")

def wait_for_port(host, port, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False

def discover_versions(base: Path):
    """Reglas: 
       1) <base>/<version>/minio existe
       2) <base>/<version> es archivo ejecutable
    """
    versions = []
    if not base.exists():
        return versions
    for entry in sorted(base.iterdir()):
        name = entry.name
        # salta archivos ocultos u otros
        if name.startswith("."):
            continue
        vdir = entry / "minio"
        if vdir.exists():
            versions.append(name)
        elif entry.is_file() and os.access(entry, os.X_OK):
            versions.append(name)
    return versions

def run_minio(version: str):
    cmd = ["python3", EXEC_MINIO, version]
    print(f"\n▶️  Launching MinIO {version}…")
    proc = subprocess.Popen(
        cmd,
        env=ENV,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1
    )
    # espera readiness del puerto SIN bloquear al orquestador
    if not wait_for_port(HOST, PORT, timeout=40):
        print("❌ MinIO no abrió :9000 a tiempo")
        # opcional: muestra algo de la salida de execute_minio
        try:
            tail = "".join((proc.stdout.read() or "")[-2000:])
            if tail:
                print(tail)
        except Exception:
            pass
        try:
            proc.terminate(); proc.wait(timeout=5)
        except Exception:
            pass
        return None
    return proc

def stop_minio():
    # Mata cualquier proceso 'minio' (igual que tu script hace en kill)
    subprocess.run(["pkill", "-9", "-x", "minio"], text=True)

def run_warp_and_get_avg():
    print("🚀 Running warp benchmark…")
    proc = subprocess.Popen(
        ["python3", EXEC_WARP],
        env=ENV,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1
    )
    collected = []
    for line in iter(proc.stdout.readline, ""):
        print(line, end="")   # salida en vivo
        collected.append(line)
    proc.wait()
    out = "".join(collected)
    m = AVG_RE.search(out)
    if not m:
        return None
    return float(m.group(1))

def append_csv_row(version: str, avg: float):
    newfile = not Path(CSV_OUT).exists()
    with open(CSV_OUT, "a", newline="") as f:
        w = csv.writer(f)
        if newfile:
            w.writerow(["version", "MiBps"])
        w.writerow([version, avg])

def main():
    versions = discover_versions(BASE)
    if not versions:
        print(f"No encontré versiones en {BASE}")
        return

    print(f"Encontré {len(versions)} versiones:\n- " + "\n- ".join(versions))

    for v in versions:
        minio_proc = None
        try:
            minio_proc = run_minio(v)
            if not minio_proc:
                continue
            avg = run_warp_and_get_avg()
            ...
        finally:
            print("🛑 Deteniendo MinIO…")
            stop_minio()
            if minio_proc:
                try:
                    minio_proc.terminate()
                    minio_proc.wait(timeout=5)
                except Exception:
                    pass
            time.sleep(1)

if __name__ == "__main__":
    main()
