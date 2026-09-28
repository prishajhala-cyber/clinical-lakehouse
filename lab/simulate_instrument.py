"""Simulate a protein design lab: a design registry, LIMS plate maps, and a plate reader.

Usage (from the project root):
    python lab/simulate_instrument.py reference   # create designs and plate maps
    python lab/simulate_instrument.py run 1       # the instrument finishes run 1
    python lab/simulate_instrument.py all         # every run, in order
"""
import csv
import json
import os
import pathlib
import random
import sys
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "lab_reference"
PLATE_MAP_DIR = REFERENCE_DIR / "plate_maps"
OUTBOX = ROOT / "instrument_share" / "outbox"

ROWS = "ABCDEFGH"
COLUMNS = range(1, 13)
DESIGNS_PER_PLATE = 80
PLATES = ["PLT-0001", "PLT-0002", "PLT-0003", "PLT-0004", "PLT-0005"]
AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"

# Each run is one scenario. Several are deliberately messy, like real lab data.
RUNS = {
    1: {"run_id": "RUN-0001", "plate_id": "PLT-0001", "firmware": "2.4.1", "scenario": "normal"},
    2: {"run_id": "RUN-0002", "plate_id": "PLT-0002", "firmware": "2.4.1", "scenario": "normal"},
    3: {"run_id": "RUN-0003", "plate_id": "PLT-0003", "firmware": "3.0.0", "scenario": "firmware_drift"},
    4: {"run_id": "RUN-0004", "plate_id": "PLT-0004", "firmware": "2.4.1", "scenario": "failed_assay"},
    5: {"run_id": "RUN-0005", "plate_id": "PLT-0005", "firmware": "2.4.1", "scenario": "corrupt_reading"},
    6: {"run_id": "RUN-0002", "plate_id": "PLT-0002", "firmware": "2.4.1", "scenario": "reexport"},
}


def well_layout():
    """Standard layout: column 1 positive controls, column 12 negative controls, designs between."""
    layout = []
    for row in ROWS:
        for col in COLUMNS:
            if col == 1:
                sample_type = "positive_control"
            elif col == 12:
                sample_type = "negative_control"
            else:
                sample_type = "design"
            layout.append((f"{row}{col}", sample_type))
    return layout


# ---------- Reference data: the Design stage and the LIMS ----------

def create_reference():
    rng = random.Random(42)
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    PLATE_MAP_DIR.mkdir(parents=True, exist_ok=True)

    designs = []
    for i in range(1, DESIGNS_PER_PLATE * len(PLATES) + 1):
        length = rng.randint(60, 90)
        designs.append({
            "design_id": f"DSN-{i:04d}",
            "target": "TGT-IL23R",
            "design_method": "backbone_generation+sequence_design",
            "model_version": rng.choice(["v1.2", "v1.3"]),
            "sequence": "M" + "".join(rng.choice(AMINO_ACIDS) for _ in range(length - 1)),
        })
    with open(REFERENCE_DIR / "designs.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=designs[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(designs)

    design_iter = iter(designs)
    for plate_id in PLATES:
        rows = []
        for well, sample_type in well_layout():
            design = next(design_iter) if sample_type == "design" else None
            rows.append({
                "plate_id": plate_id,
                "well": well,
                "sample_type": sample_type,
                "design_id": design["design_id"] if design else "",
                "concentration_nm": 50 if design else "",
            })
        with open(PLATE_MAP_DIR / f"{plate_id}.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    print(f"Created {len(designs)} designs and {len(PLATES)} plate maps in {REFERENCE_DIR}")


# ---------- The instrument ----------

def simulate_signal(sample_type, model_version, rng, failed_assay):
    """Fluorescence signal for one well, in relative fluorescence units (RFU)."""
    if failed_assay:  # controls barely separate: the plate's assay did not work
        if sample_type == "positive_control":
            return rng.gauss(6000, 2500)
        if sample_type == "negative_control":
            return rng.gauss(2500, 1500)
        return rng.gauss(3000, 1800)

    if sample_type == "positive_control":
        return rng.gauss(20000, 800)
    if sample_type == "negative_control":
        return rng.gauss(1000, 150)

    # Designs: newer model versions produce binders more often
    binder_rate = 0.30 if model_version == "v1.3" else 0.15
    if rng.random() < binder_rate:
        strength = rng.uniform(0.4, 1.0)
        return 1000 + strength * 19000 + rng.gauss(0, 600)
    return rng.gauss(1100, 200)


def write_atomically(path, text):
    """Write to a temporary file, then rename, so a watcher never sees a half-written file."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def run_instrument(number):
    spec = RUNS[number]
    rng = random.Random(1000 + int(spec["run_id"][-4:]))  # same run ID always gives the same data
    OUTBOX.mkdir(parents=True, exist_ok=True)

    with open(REFERENCE_DIR / "designs.csv") as f:
        versions = {d["design_id"]: d["model_version"] for d in csv.DictReader(f)}
    with open(PLATE_MAP_DIR / f"{spec['plate_id']}.csv") as f:
        plate_map = {r["well"]: r for r in csv.DictReader(f)}

    readings = {}
    for well, row in plate_map.items():
        value = simulate_signal(
            row["sample_type"], versions.get(row["design_id"]), rng,
            failed_assay=spec["scenario"] == "failed_assay",
        )
        readings[well] = str(max(0, round(value)))
    if spec["scenario"] == "corrupt_reading":
        readings["D7"] = "OVRFLW"  # detector overflow, a real plate reader error code

    run_number = int(spec["run_id"][-4:])
    started = datetime(2026, 9, 28, 9, 0, tzinfo=timezone.utc) + timedelta(hours=run_number)
    plate_label = "Plate Barcode" if spec["firmware"].startswith("3.") else "Plate ID"
    lines = [
        "Instrument,PR-01",
        f"Firmware,{spec['firmware']}",
        f"Run ID,{spec['run_id']}",
        f"{plate_label},{spec['plate_id']}",
        "Read Type,Fluorescence",
        f"Read Time,{started.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "," + ",".join(str(c) for c in COLUMNS),
    ]
    for row in ROWS:
        lines.append(row + "," + ",".join(readings[f"{row}{c}"] for c in COLUMNS))

    metadata = {
        "run_id": spec["run_id"],
        "plate_id": spec["plate_id"],
        "instrument_id": "PR-01",
        "instrument_model": "LumaRead 3000",
        "firmware_version": spec["firmware"],
        "assay_type": "binding_fluorescence",
        "protocol_version": "v3",
        "operator": "jlee",
        "started_at": started.isoformat().replace("+00:00", "Z"),
    }

    stem = spec["run_id"] + ("_reexport" if spec["scenario"] == "reexport" else "")
    # Metadata first, data file last: the data file's arrival is the signal a run is complete
    write_atomically(OUTBOX / f"{stem}.meta.json", json.dumps(metadata, indent=2))
    write_atomically(OUTBOX / f"{stem}.csv", "\n".join(lines) + "\n")
    print(f"Run {number} ({spec['scenario']}): wrote {stem}.csv and {stem}.meta.json to {OUTBOX}")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "reference":
        create_reference()
    elif command == "run" and len(sys.argv) == 3 and int(sys.argv[2]) in RUNS:
        run_instrument(int(sys.argv[2]))
    elif command == "all":
        for n in RUNS:
            run_instrument(n)
    else:
        print(__doc__)
        sys.exit(1)