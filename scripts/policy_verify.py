#!/usr/bin/env python3
"""Verifica la integridad del registro de versiones congeladas de políticas.

Comprobaciones:
1. Cada entrada del manifiesto apunta a un archivo existente cuyo SHA-256 y tamaño coinciden.
2. No hay archivos huérfanos bajo policies/versions/ (todo archivo congelado debe estar
   en el manifiesto; se permiten sellos de tiempo como archivos anexos).
3. Con --against-ref REF: el manifiesto solo creció respecto de REF (ninguna entrada
   previa fue modificada ni eliminada) y ningún archivo bajo policies/versions/ fue
   modificado ni borrado respecto de REF.

Uso:
    python3 scripts/policy_verify.py [--against-ref origin/main]
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSIONS_DIR = ROOT / "policies" / "versions"
MANIFEST_PATH = ROOT / "policies" / "manifest.json"

# Archivos anexos permitidos junto a un documento congelado (evidencia de sellado).
SIDECAR_NAMES = {"timestamp.tsq", "timestamp.tsr", "timestamp.tsa.json"}
SIDECAR_SUFFIXES = {".ots"}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def is_sidecar(path: Path) -> bool:
    return path.name in SIDECAR_NAMES or path.suffix in SIDECAR_SUFFIXES


def verify_manifest() -> list[str]:
    errors: list[str] = []
    if not MANIFEST_PATH.exists():
        return ["No existe policies/manifest.json"]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    registered: set[Path] = set()

    for entry in manifest.get("entries", []):
        label = f"{entry.get('doc')} {entry.get('version')}"
        file_path = ROOT / entry["file"]
        registered.add(file_path.resolve())
        if not file_path.is_file():
            errors.append(f"{label}: falta el archivo {entry['file']}")
            continue
        digest = sha256_of(file_path)
        if digest != entry["sha256"]:
            errors.append(
                f"{label}: HASH NO COINCIDE en {entry['file']}\n"
                f"    manifiesto: {entry['sha256']}\n"
                f"    archivo   : {digest}"
            )
        if file_path.stat().st_size != entry["bytes"]:
            errors.append(f"{label}: tamaño no coincide en {entry['file']}")

    if VERSIONS_DIR.exists():
        for path in sorted(VERSIONS_DIR.rglob("*")):
            if path.is_file() and not is_sidecar(path) and path.resolve() not in registered:
                errors.append(f"Archivo no registrado en el manifiesto: {path.relative_to(ROOT)}")
    return errors


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout


def verify_against_ref(ref: str) -> list[str]:
    errors: list[str] = []

    # 1. El manifiesto solo puede crecer: toda entrada previa debe seguir idéntica.
    try:
        old_manifest = json.loads(git("show", f"{ref}:policies/manifest.json"))
    except subprocess.CalledProcessError:
        old_manifest = None  # el manifiesto no existía en REF; nada que comparar
    if old_manifest is not None:
        current = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) if MANIFEST_PATH.exists() else {"entries": []}
        current_by_key = {(e["doc"], e["version"]): e for e in current.get("entries", [])}
        for old in old_manifest.get("entries", []):
            key = (old["doc"], old["version"])
            if key not in current_by_key:
                errors.append(f"Entrada eliminada del manifiesto: {key[0]} {key[1]}")
            elif current_by_key[key] != old:
                errors.append(f"Entrada modificada en el manifiesto: {key[0]} {key[1]}")

    # 2. Bajo policies/versions/ solo se permiten adiciones respecto de REF.
    diff = git("diff", "--name-status", ref, "--", "policies/versions/")
    for line in diff.splitlines():
        status, _, path = line.partition("\t")
        if status and status[0] != "A":
            errors.append(f"Cambio prohibido ({status}) en versión congelada: {path}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--against-ref", help="Ref de git contra el cual verificar inmutabilidad (ej: origin/main)")
    args = parser.parse_args()

    errors = verify_manifest()
    if args.against_ref:
        errors += verify_against_ref(args.against_ref)

    if errors:
        print("FALLÓ la verificación de integridad de políticas:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) if MANIFEST_PATH.exists() else {"entries": []}
    print(f"OK: {len(manifest.get('entries', []))} versión(es) congelada(s) verificada(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
