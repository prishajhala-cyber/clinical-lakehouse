"""Simulate a second source system: a lab that sends HL7 v2 ORU^R01 messages.

Reads Synthea's FHIR export and writes some patients' lab results as HL7 v2
messages, one per file. These results also exist in the FHIR data, so the same
result arrives from two systems, which the Silver layer must deduplicate.
"""
import json
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
FHIR_DIR = ROOT / "data" / "synthea" / "fhir"
OUT_DIR = ROOT / "data" / "hl7"
LABS_PER_PATIENT = 30

def hl7_timestamp(iso_string):
    """Convert a FHIR timestamp to HL7 format, in UTC.

    '2018-05-11T01:55:02+00:00' -> '20180511015502'
    """
    dt = datetime.fromisoformat(iso_string).astimezone(timezone.utc)
    return dt.strftime("%Y%m%d%H%M%S")

def is_numeric_lab_result(obs):
    """True if this Observation is a lab result with a numeric value."""
    category = obs.get("category", [{}])[0].get("coding", [{}])[0].get("code")
    return category == "laboratory" and "valueQuantity" in obs

def build_oru(patient, obs):
    """Build one HL7 v2.5.1 ORU^R01 message for a single lab result."""
    coding = obs["code"]["coding"][0]
    quantity = obs["valueQuantity"]
    ts = hl7_timestamp(obs["effectiveDateTime"])
    name = patient["name"][0]
    control_id = obs["id"].replace("-", "")

    segments = [
        f"MSH|^~\\&|LABSYS|MAINLAB|EHR|HOSPITAL|{ts}||ORU^R01|{control_id}|P|2.5.1",
        f"PID|1||{patient['id']}^^^SYNTHEA^MR||{name['family']}^{name['given'][0]}",
        f"OBR|1|||{coding['code']}^{coding['display']}^LN|||{ts}",
        f"OBX|1|NM|{coding['code']}^{coding['display']}^LN||{quantity['value']}"
        f"|{quantity.get('unit', '')}|||||F|||{ts}",
    ]
    return "\r".join(segments)

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load every patient, then keep every other one as a "lab system" patient
    with open(FHIR_DIR / "Patient.ndjson") as f:
        patients = [json.loads(line) for line in f]
    lab_patients = {p["id"]: p for p in patients[::2]}

    # Walk through observations, writing messages for lab patients' results
    written = {patient_id: 0 for patient_id in lab_patients}
    with open(FHIR_DIR / "Observation.ndjson") as f:
        for line in f:
            obs = json.loads(line)
            patient_id = obs["subject"]["reference"].split("/")[-1]

            if patient_id not in lab_patients or not is_numeric_lab_result(obs):
                continue
            if written[patient_id] >= LABS_PER_PATIENT:
                continue

            message = build_oru(lab_patients[patient_id], obs)
            (OUT_DIR / f"{obs['id']}.hl7").write_text(message)
            written[patient_id] += 1

    total = sum(written.values())
    print(f"Wrote {total} HL7 messages for {len(lab_patients)} patients to {OUT_DIR}")


if __name__ == "__main__":
    main()