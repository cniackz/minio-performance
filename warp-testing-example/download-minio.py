# save as download_minio_binaries.py
import os
import re
import stat
import urllib.request
import urllib.error

BASE_URL = "https://dl.min.io/aistor/minio/release/darwin-arm64/archive/"
DEST_DIR = "/Users/cniackz/minio_versions"

EXCLUDE_SUFFIXES = (".asc", ".minisig", ".sha256sum")

def list_index_files():
    req = urllib.request.Request(BASE_URL)
    with urllib.request.urlopen(req, timeout=60) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    # Extrae todos los href del índice
    candidates = re.findall(r'href="([^"]+)"', html)
    files = []
    for href in candidates:
        # Ignora directorios y padres
        if href.endswith("/"):
            continue
        # Solo archivos que empiezan con "minio"
        if not href.startswith("minio"):
            continue
        # Excluir firmas/sumas
        if href.endswith(EXCLUDE_SUFFIXES):
            continue
        files.append(href)
    return sorted(set(files))

def dest_for(filename: str) -> str:
    """
    filename: 'minio' o 'minio.RELEASE.2025-07-30T15-53-03Z'
    Devuelve la ruta de carpeta destino y el path final del binario.
    """
    if filename == "minio":
        folder = os.path.join(DEST_DIR, "latest")
    elif filename.startswith("minio.RELEASE."):
        version = filename[len("minio."):].strip()
        folder = os.path.join(DEST_DIR, version)
    else:
        # fallback: carpeta con el nombre del archivo
        folder = os.path.join(DEST_DIR, filename)
    os.makedirs(folder, exist_ok=True)
    return folder, os.path.join(folder, "minio")

def download_file(url: str, out_path: str):
    tmp_path = out_path + ".part"
    try:
        with urllib.request.urlopen(url, timeout=300) as r, open(tmp_path, "wb") as f:
            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
        os.replace(tmp_path, out_path)
    except Exception:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        finally:
            raise

def main():
    os.makedirs(DEST_DIR, exist_ok=True)
    files = list_index_files()
    if not files:
        print("No se encontraron archivos válidos en el índice.")
        return
    print(f"Encontrados {len(files)} binarios para descargar.")

    for fname in files:
        folder, bin_path = dest_for(fname)
        if os.path.exists(bin_path):
            print(f"✅ Ya existe: {bin_path}")
            continue
        url = BASE_URL + fname
        print(f"⬇️ {fname} → {bin_path}")
        try:
            download_file(url, bin_path)
            # chmod +x
            os.chmod(bin_path, os.stat(bin_path).st_mode | stat.S_IEXEC)
            print(f"✔ Listo: {bin_path}")
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP {e.code} al descargar {fname}")
        except Exception as e:
            print(f"❌ Error con {fname}: {e}")

if __name__ == "__main__":
    main()
