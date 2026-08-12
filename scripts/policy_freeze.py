#!/usr/bin/env python3
"""Congela una versión inmutable de un documento legal y la registra en policies/manifest.json.

Uso:
    python3 scripts/policy_freeze.py <archivo-fuente> --doc <id-doc> --version vX.Y.Z --title "Título"

Ejemplo:
    python3 scripts/policy_freeze.py privacy.html --doc privacy --version v1.0.0 --title "Política de Privacidad"

Reglas:
- Una versión congelada nunca se modifica ni se elimina; un cambio de texto es una versión nueva.
- El hash SHA-256 registrado corresponde a los bytes exactos del archivo congelado.
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICIES_DIR = ROOT / "policies"
VERSIONS_DIR = POLICIES_DIR / "versions"
MANIFEST_PATH = POLICIES_DIR / "manifest.json"

VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+$")
DOC_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {"_comment": "Registro de versiones congeladas de documentos legales. Solo se agregan entradas; nunca se modifican ni eliminan.", "entries": []}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", help="Archivo fuente a congelar (ej: privacy.html)")
    parser.add_argument("--doc", required=True, help="Identificador del documento (ej: privacy, datos-personales)")
    parser.add_argument("--version", required=True, help="Versión semántica con prefijo v (ej: v1.0.0)")
    parser.add_argument("--title", required=True, help="Título humano del documento")
    args = parser.parse_args()

    if not VERSION_RE.match(args.version):
        print(f"ERROR: versión inválida '{args.version}' (formato esperado: vX.Y.Z)", file=sys.stderr)
        return 1
    if not DOC_ID_RE.match(args.doc):
        print(f"ERROR: id de documento inválido '{args.doc}' (minúsculas, dígitos y guiones)", file=sys.stderr)
        return 1

    source = Path(args.source)
    if not source.is_absolute():
        source = ROOT / args.source
    if not source.is_file():
        print(f"ERROR: no existe el archivo fuente {source}", file=sys.stderr)
        return 1

    dest_dir = VERSIONS_DIR / args.doc / args.version
    if dest_dir.exists():
        print(f"ERROR: {dest_dir.relative_to(ROOT)} ya existe. Las versiones congeladas son inmutables; use una versión nueva.", file=sys.stderr)
        return 1

    manifest = load_manifest()
    for entry in manifest["entries"]:
        if entry["doc"] == args.doc and entry["version"] == args.version:
            print(f"ERROR: {args.doc} {args.version} ya está registrado en el manifiesto.", file=sys.stderr)
            return 1

    dest_dir.mkdir(parents=True)
    dest = dest_dir / source.name
    shutil.copyfile(source, dest)

    digest = sha256_of(dest)
    entry = {
        "doc": args.doc,
        "version": args.version,
        "title": args.title,
        "file": str(dest.relative_to(ROOT)),
        "sha256": digest,
        "bytes": dest.stat().st_size,
        "frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else str(source),
    }
    manifest["entries"].append(entry)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Congelado: {args.doc} {args.version}")
    print(f"  archivo : {entry['file']}")
    print(f"  sha256  : {digest}")
    print()
    print("Siguientes pasos:")
    print(f"  1. Sellar con la TSA:   scripts/timestamp_rfc3161.sh {args.doc} {args.version}")
    print(f"  2. Anclar (opcional):   scripts/anchor_opentimestamps.sh {args.doc} {args.version}")
    print("  3. Commit + tag firmado: git tag -s policy/" + f"{args.doc}-{args.version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
