"""Land raw files in the Snowflake stage (the Bronze landing zone).

- FHIR: Synthea's NDJSON files are uploaded as-is.
- HL7 v2: each raw message is uploaded as-is, AND parsed into JSON, because
  pipe-delimited text is painful to parse in SQL (parsing at the edge).

File names are stable and PUT skips files already in the stage, so running
this script again never creates duplicates (idempotent).
"""
import json

from sf import ROOT, connect

FHIR_DIR = ROOT / "data" / "synthea" / "fhir"
HL7_DIR = ROOT / "data" / "hl7"
PARSED_DIR = ROOT / "data" / "hl7_parsed"

def parse_oru(text, source_file):
    """Parse one HL7 v2 ORU^R01 message into a flat dictionary.

    MSH quirk: the field separator itself counts as MSH-1, so after splitting
    on '|', index N holds MSH-(N+1). MSH-10 (message control ID) is index 9.
    Every other segment lines up normally: OBX-5 is index 5.
    """
    segments = {}
    for line in text.splitlines():
        if line:
            fields = line.split("|")
            segments[fields[0]] = fields

    msh, pid, obx = segments["MSH"], segments["PID"], segments["OBX"]
    test_code, test_name = (obx[3].split("^") + ["", ""])[:2]

    return {
        "message_control_id": msh[9],
        "message_type": msh[8],
        "sending_application": msh[2],
        "patient_id": pid[3].split("^")[0],
        "loinc_code": test_code,
        "loinc_display": test_name,
        "value": obx[5],
        "unit": obx[6],
        "result_status": obx[11],
        "observed_at": obx[14],
        "source_file": source_file,
    }

def write_parsed_hl7():
    """Parse every HL7 message and save each as a JSON file."""
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(HL7_DIR.glob("*.hl7"))
    for path in files:
        record = parse_oru(path.read_text(), path.name)
        (PARSED_DIR / f"{path.stem}.json").write_text(json.dumps(record))
    return len(files)

def put_files(cursor, local_pattern, stage_folder):
    """Upload local files matching a pattern into a stage folder.

    PUT skips files that already exist in the stage (OVERWRITE=FALSE),
    so re-running never duplicates anything.
    """
    results = cursor.execute(
        f"PUT 'file://{local_pattern}' @landing/{stage_folder}/ "
        f"AUTO_COMPRESS=TRUE OVERWRITE=FALSE"
    ).fetchall()
    uploaded = sum(1 for row in results if row[6] == "UPLOADED")
    skipped = sum(1 for row in results if row[6] == "SKIPPED")
    print(f"  {stage_folder}: {uploaded} uploaded, {skipped} skipped (already in stage)")

def main():
    count = write_parsed_hl7()
    print(f"Parsed {count} HL7 messages into {PARSED_DIR}")

    print("Uploading to @landing:")
    conn = connect()
    try:
        cursor = conn.cursor()
        put_files(cursor, FHIR_DIR / "Patient.ndjson", "fhir/Patient")
        put_files(cursor, FHIR_DIR / "Observation.ndjson", "fhir/Observation")
        put_files(cursor, HL7_DIR / "*.hl7", "hl7_raw")
        put_files(cursor, PARSED_DIR / "*.json", "hl7_parsed")
    finally:
        conn.close()


if __name__ == "__main__":
    main()