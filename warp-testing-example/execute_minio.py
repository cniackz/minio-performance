
#!/usr/bin/env python3
"""
execute_minio.py — pick a MinIO version, kill any running MinIO, optionally clean volumes,
and launch the requested binary.

Usage:
  python3 execute_minio.py <MINIO_VERSION> [--base ~/minio_versions] [--no-clean]
                           [--clean-cmd 'clean_minio_vols'] [--daemon]
                           [--dry-run] [--] [MINIO_ARGS ...]

Examples:
  python3 execute_minio.py latest -- server --address :9000 /tmp/data{1...4}
  python3 execute_minio.py RELEASE.2025-07-29T06-52-30Z -- --address :9000 /data

Notes:
- By default it assumes your versions live in ~/minio_versions and each entry is either:
    a) a directory containing a binary named 'minio', or
    b) an executable file itself (named exactly like the version, or 'minio').
- It tries to kill existing MinIO processes with multiple strategies (pkill/pgrep/kill).
- It runs a shell command called 'clean_minio_vols' unless you pass --no-clean or change it with --clean-cmd.
"""

import argparse
import os
import shlex
import stat
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

def run(cmd: List[str], check: bool = False, capture: bool = False, shell: bool = False, env=None):
    try:
        if shell:
            proc = subprocess.run(" ".join(cmd), shell=True, check=check, text=True, capture_output=capture, env=env)
        else:
            proc = subprocess.run(cmd, check=check, text=True, capture_output=capture, env=env)
        return proc
    except FileNotFoundError:
        return subprocess.CompletedProcess(cmd, returncode=127, stdout="", stderr=f"Command not found: {cmd[0]}")

def ensure_exec(path: Path):
    try:
        mode = path.stat().st_mode
        if not (mode & stat.S_IXUSR):
            path.chmod(mode | stat.S_IXUSR)
    except Exception:
        pass

def find_minio_binary(base: Path, version: str) -> Path:
    # 1) <base>/<version>/minio
    p = base / version / "minio"
    if p.exists():
        return p
    # 2) <base>/<version> (as a standalone binary named by version)
    p = base / version
    if p.exists() and p.is_file():
        return p
    # 3) <base>/latest/minio if user passed "latest"
    if version == "latest":
        p = base / "latest" / "minio"
        if p.exists():
            return p
        p = base / "latest"
        if p.exists() and p.is_file():
            return p
    # 4) <base>/minio (fallback)
    p = base / "minio"
    if p.exists():
        return p
    raise FileNotFoundError(f"Could not locate a MinIO binary for version '{version}' under {base}")

def pids_for_minio() -> List[int]:
    # Use pgrep first
    out = run(["pgrep", "-f", "([/ ]|^)minio([ ]|$)"], capture=True)
    pids = []
    if out.returncode == 0 and out.stdout.strip():
        pids.extend([int(x) for x in out.stdout.strip().splitlines() if x.strip().isdigit()])
    else:
        # Fallback: parse ps output
        ps = run(["ps", "-axo", "pid,comm,args"], capture=True)
        if ps.returncode == 0:
            for line in ps.stdout.splitlines():
                try:
                    pid_str, *_rest = line.strip().split(None, 2)
                    if not pid_str.isdigit():
                        continue
                    if " minio " in line or line.strip().endswith(" minio") or "/minio " in line or line.strip().endswith("/minio"):
                        pids.append(int(pid_str))
                except Exception:
                    continue
    # Exclude our own PID
    me = os.getpid()
    return [pid for pid in pids if pid != me]

def kill_minio(verbose: bool = True) -> None:
    pids = pids_for_minio()
    if not pids:
        if verbose:
            print("No running MinIO processes found.")
        return
    if verbose:
        print(f"Found MinIO PIDs: {pids}. Sending SIGKILL...")
    # Try pkill by name first
    run(["pkill", "-9", "-x", "minio"])
    # And direct kill for any remaining
    for pid in pids_for_minio():
        run(["kill", "-9", str(pid)])
    if verbose:
        print("Kill attempts complete.")

# --- helpers de limpieza en Python ---
from pathlib import Path
import shutil

DATA_DIRS = [Path(f"/Volumes/data{i}") for i in range(1, 5)]

def _safe_clear_dir(dir_path: Path):
    """Borra TODO el contenido del directorio (archivos, carpetas, enlaces),
    pero NO borra el directorio root en sí."""
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        return
    # Recorre contenido y elimina cada entrada
    for entry in dir_path.iterdir():
        try:
            if entry.is_symlink() or entry.is_file():
                entry.unlink(missing_ok=True)
            elif entry.is_dir():
                shutil.rmtree(entry, ignore_errors=True)
            else:
                # fallback
                entry.unlink(missing_ok=True)
        except Exception:
            # no detenemos el proceso por errores individuales
            pass

def python_clean_minio_vols():
    # 1) Borra contenido normal
    for d in DATA_DIRS:
        _safe_clear_dir(d)
    # 2) Asegura que no quede .minio.sys (si existe como carpeta/archivo)
    for d in DATA_DIRS:
        msys = d / ".minio.sys"
        if msys.exists():
            try:
                if msys.is_dir():
                    shutil.rmtree(msys, ignore_errors=True)
                else:
                    msys.unlink(missing_ok=True)
            except Exception:
                pass

# --- reemplaza tu run_clean por este ---
def run_clean(clean_cmd: Optional[str], dry_run: bool = False) -> None:
    """Si el clean_cmd es 'clean_minio_vols', usa la versión Python.
    Si no, ejecuta el comando tal cual (compatibilidad)."""
    if not clean_cmd:
        return

    if clean_cmd.strip() == "clean_minio_vols":
        if dry_run:
            print("[dry-run] Would run python_clean_minio_vols()")
            return
        print("Running clean (Python): clean_minio_vols")
        python_clean_minio_vols()
        return

    # Fallback: comando externo (cuando quieras otra cosa explícita)
    cmd = f"{clean_cmd}"
    shell_cmd = ["/bin/bash", "-lc", cmd]
    if dry_run:
        print(f"[dry-run] Would run clean command: {' '.join(shell_cmd)}")
        return
    print(f"Running clean command: {cmd}")
    proc = subprocess.run(shell_cmd, text=True)
    if proc.returncode != 0:
        print(f"Warning: clean command exited with code {proc.returncode}")

def launch_minio(binary: Path, args: List[str], dry_run: bool) -> int:
    ensure_exec(binary)
    cmd = [str(binary)] + args
    if dry_run:
        print(f"[dry-run] Would execute: {' '.join(shlex.quote(c) for c in cmd)}")
        return 0

    print(f"Starting MinIO (foreground): {' '.join(shlex.quote(c) for c in cmd)}")
    print(f"[DEBUG] Launching foreground command: {' '.join(shlex.quote(c) for c in cmd)}")
    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
        return proc.returncode
    except KeyboardInterrupt:
        try:
            proc.terminate()
        except Exception:
            pass
        return 130

def main():
    parser = argparse.ArgumentParser(description="Switch and run a specific MinIO version.")
    parser.add_argument("version", help="Version folder/file under the base path (e.g., latest or RELEASE.2025-07-29T06-52-30Z)")
    parser.add_argument("--base", default="~/minio_versions", help="Base directory containing versions (default: ~/minio_versions)")
    parser.add_argument("--no-clean", action="store_true", help="Skip running clean command before start")
    parser.add_argument("--clean-cmd", default="clean_minio_vols", help="Shell command/function to clean disks (default: clean_minio_vols)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen without doing it")
    parser.add_argument("--", dest="sep", nargs="*", help=argparse.SUPPRESS)  # accept bare --
    parser.add_argument("minio_args", nargs=argparse.REMAINDER, help="Arguments passed to MinIO after --")
    args = parser.parse_args()

    base = Path(os.path.expanduser(args.base))
    version = args.version.strip()

    # Guardar versión para que otros scripts la lean
    Path("/tmp/minio_version.txt").write_text(version)

    try:
        binary = find_minio_binary(base, version)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)

    print(f"Using MinIO binary: {binary}")
    # 1) Kill existing
    kill_minio(verbose=True)
    # 2) Clean
    if not args.no_clean:
        run_clean(args.clean_cmd, dry_run=args.dry_run)
    else:
        print("Skipping clean command (--no-clean).")

    # 3) Launch
    # Remove leading '--' if present in args.minio_args


    DEFAULT_MINIO_ARGS = [
        "server",
        "/Volumes/data{1...4}",
        "--address", ":9000",
        "--console-address", ":9001",
        "--license", "/usr/local/bin/minio.license"
    ]

    # inside main()
    passed_args = args.minio_args
    if passed_args and passed_args[0] == "--":
        passed_args = passed_args[1:]

    if not passed_args:
        passed_args = DEFAULT_MINIO_ARGS

    code = launch_minio(binary, passed_args, dry_run=args.dry_run)
    print(f"MinIO exited with code {code}")
    sys.exit(0 if args.daemon or code == 0 else code)

if __name__ == "__main__":
    main()
