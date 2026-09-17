"""Ekspor kontrak OpenAPI ke file, supaya perubahannya terlihat di PR.

Jalankan setiap kali kalian mengubah schemas.py atau menambah endpoint:

    python scripts/export_openapi.py

Lalu commit file openapi.json yang dihasilkan, di PR yang sama dengan
perubahan schema-nya. Dengan begitu reviewer bisa melihat persis apa
yang berubah di kontrak, dan frontend tahu kapan harus regenerate tipe.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402

OUTPUT = ROOT / "openapi.json"


def main() -> None:
    schema = app.openapi()
    OUTPUT.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Kontrak OpenAPI ditulis ke {OUTPUT}")
    print(f"Jumlah path: {len(schema['paths'])}")


if __name__ == "__main__":
    main()
