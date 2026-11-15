from pathlib import Path
import csv
import json
from datetime import datetime, timezone

RAW = Path("data/raw/FLEX_PSI69/FLEX-007")
OUT = Path("data/processed/telemetry/FLEX-007")

OUT.mkdir(parents=True, exist_ok=True)

CONFIG = {
    "ColorCamData": [
        "time_s", "flame_diameter_mm", "flame_standoff_mm"
    ],
    "DropletData": [
        "time_s", "droplet_diameter_mm",
        "droplet_x_mm", "droplet_y_mm"
    ],
    "LLUVData": [
        "time_s", "flame_diameter_mm",
        "flame_standoff_mm", "droplet_x_mm", "droplet_z_mm"
    ],
}

report = {
    "experiment": "FLEX-007",
    "mission": "FLEX PSI-69",
    "processed_at": datetime.now(timezone.utc).isoformat(),
    "sensors": {},
    "warnings": [],
}

def process_file(name, columns):
    source = RAW / f"FLEX-007_{name}.txt"
    destination = OUT / f"{name}.csv"

    if not source.exists():
        report["warnings"].append(f"Ficheiro não encontrado: {source}")
        return

    rows = []
    invalid = []

    lines = source.read_text(encoding="utf-8-sig").splitlines()

    for line_number, line in enumerate(lines[1:], start=2):
        parts = line.split()

        if not parts:
            continue

        # LLUV: quando faltam 4 valores, o standoff está ausente.
        if name == "LLUVData" and len(parts) == 4:
            parts.insert(2, "")

        # Sensores com campos finais ausentes.
        if name in ("ColorCamData", "DropletData"):
            if len(parts) < len(columns):
                parts += [""] * (len(columns) - len(parts))

        if len(parts) != len(columns):
            invalid.append({
                "line": line_number,
                "values": parts
            })
            continue

        record = {}
        valid = True

        for column, value in zip(columns, parts):
            if value == "":
                record[column] = None
                continue

            try:
                record[column] = float(value)
            except ValueError:
                valid = False
                break

        if valid:
            rows.append(record)
        else:
            invalid.append({
                "line": line_number,
                "values": parts
            })

    with destination.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    missing = {
        column: sum(row[column] is None for row in rows)
        for column in columns
    }

    report["sensors"][name] = {
        "source": str(source),
        "output": str(destination),
        "rows_processed": len(rows),
        "invalid_rows": len(invalid),
        "missing_values": missing,
        "invalid_examples": invalid[:10],
    }

    print(f"\n[{name}]")
    print(f"Registos processados: {len(rows)}")
    print(f"Linhas inválidas: {len(invalid)}")
    print(f"Valores ausentes: {missing}")
    print(f"CSV: {destination}")

for name, columns in CONFIG.items():
    process_file(name, columns)

test_sheet = RAW / "FLEX-007_TestSheet.txt"

if test_sheet.exists():
    destination = OUT / "TestSheet.txt"
    destination.write_text(
        test_sheet.read_text(encoding="utf-8-sig"),
        encoding="utf-8"
    )
    report["test_sheet"] = str(destination)

report_path = OUT / "relatorio_etl.json"
report_path.write_text(
    json.dumps(report, indent=4, ensure_ascii=False),
    encoding="utf-8"
)

print("\n====================================")
print("ETL FLEX-007 CONCLUÍDO")
print("====================================")
print(f"Relatório: {report_path}")
print(f"Diretório: {OUT}")
print(json.dumps(report["sensors"], indent=2, ensure_ascii=False))
