from pathlib import Path

base_path = Path.home() / "minio_versions"
if base_path.exists():
    versions = sorted([p.name for p in base_path.iterdir() if not p.name.startswith(".")], reverse=True)
    for v in versions:
        print(v)
else:
    print(f"No existe {base_path}")
