import json
import requests
from datetime import datetime, timezone
from pathlib import Path

OPENEMR_BASE      = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
PRIMARY_CARE_BASE = "http://159.203.105.138:8080/fhir"

SEARCH_GENDER = "male"
SEARCH_GIVEN  = "David"
SEARCH_FAMILY = "Abshire"

SNOMED_SYSTEM = "http://snomed.info/sct"
LOINC_SYSTEM  = "http://loinc.org"

PROCEDURE_CODE    = "399208008"
PROCEDURE_DISPLAY = "Plain X-ray of chest (procedure)"

PROCEDURE_SITE_CODE    = "51185008"
PROCEDURE_SITE_DISPLAY = "Thoracic structure (body structure)"

data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)

def get_access_token():
    with open(data_dir / "access_token.json", "r") as f:
        return json.load(f).get("access_token")

def get_openemr_headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Accept": "application/json"
    }

def get_primary_care_headers():
    return {
        "Content-Type": "application/fhir+json",
        "Accept":        "application/fhir+json"
    }

def search_patient():
    url    = f"{OPENEMR_BASE}/Patient"
    params = {"given": SEARCH_GIVEN, "family": SEARCH_FAMILY, "gender": SEARCH_GENDER}

    print("Patient Discovery — OpenEMR")
    print(f"Request : GET /Patient?given={SEARCH_GIVEN}&family={SEARCH_FAMILY}&gender={SEARCH_GENDER}")

    response = requests.get(url=url, headers=get_openemr_headers(), params=params)
    entries  = response.json().get("entry", [])

    print(f"  Result  : {len(entries)} candidate(s) returned.\n")
    for i, e in enumerate(entries[:10]):
        r = e["resource"]
        n = r.get("name", [{}])[0]
        print(f"[{i}] ID: {r.get('id')} | {n.get('given',[''])[0]} {n.get('family','')} | "
              f"Gender: {r.get('gender')} | DOB: {r.get('birthDate')} | "
              f"Deceased: {r.get('deceasedBoolean') or r.get('deceasedDateTime')}")

    return entries

def get_patient_encounters(patient_id):
    url    = f"{OPENEMR_BASE}/Encounter"
    params = {"patient": patient_id, "_count": 50}

    print(f"Encounter Listing — Patient ID: {patient_id}")
    print(f"Request : GET /Encounter?patient={patient_id}&_count=50")

    response = requests.get(url=url, headers=get_openemr_headers(), params=params)
    entries  = response.json().get("entry", [])

    print(f"Total encounters found: {len(entries)}\n")

    if not entries:
        print("  WARNING: No encounters documented for this patient.")
        return None

    for i, entry in enumerate(entries):
        r = entry["resource"]
        type_display = "unknown"
        for t in r.get("type", []):
            for coding in t.get("coding", []):
                if coding.get("display"):
                    type_display = coding["display"]
                    break
            if type_display != "unknown":
                break
            if t.get("text"):
                type_display = t["text"]
                break

        reason_display = "—"
        for rc in r.get("reasonCode", []):
            for coding in rc.get("coding", []):
                if coding.get("display"):
                    reason_display = coding["display"]
                    break
            if reason_display != "—":
                break
            if rc.get("text"):
                reason_display = rc["text"]
                break

        status       = r.get("status", "unknown")
        period_start = r.get("period", {}).get("start", "unknown")
        enc_class    = r.get("class", {}).get("code", "unknown")

        print(f"  [{i}] ID: {r.get('id','—')} | Type: {type_display} | "
              f"Reason: {reason_display} | Class: {enc_class} | "
              f"Status: {status} | Date: {period_start}")

    return entries

def select_procedure_from_encounters(entries, openemr_patient_id):
    print("Procedure Selection from Encounter List")

    if entries:
        KEYWORDS = ("pulmonary", "spirometry", "lung", "respiratory",
                    "bronch", "copd", "obstructive")

        for entry in entries:
            r = entry["resource"]

            search_text = " ".join([
                t.get("coding", [{}])[0].get("display", "") or t.get("text", "")
                for t in r.get("type", [])
            ] + [
                rc.get("coding", [{}])[0].get("display", "") or rc.get("text", "")
                for rc in r.get("reasonCode", [])
            ]).lower()

            if any(kw in search_text for kw in KEYWORDS):
                print(f"  Keyword match found  : ID {r.get('id')} — {search_text[:80]}")
                return r
        fallback = entries[0]["resource"]
        print(f"  No keyword match. Using first encounter : ID {fallback.get('id')}")
        return fallback
    print(f"No encounters found for patient {openemr_patient_id}.")
    print(f"Creating a Plain X-ray of chest Procedure record on Primary Care EHR...")

    performed_dt  = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    new_procedure = {
        "resourceType": "Procedure",
        "status": "completed",
        "code": {
            "coding": [
                {
                    "system":  SNOMED_SYSTEM,
                    "code":    PROCEDURE_CODE,
                    "display": PROCEDURE_DISPLAY
                }
            ],
            "text": PROCEDURE_DISPLAY
        },
        "subject":           {"reference": f"Patient/{openemr_patient_id}"},
        "performedDateTime": performed_dt,
        "bodySite": [
            {
                "coding": [
                    {
                        "system":  SNOMED_SYSTEM,
                        "code":    PROCEDURE_SITE_CODE,
                        "display": PROCEDURE_SITE_DISPLAY
                    }
                ]
            }
        ]
    }

    create_response = requests.post(
        f"{PRIMARY_CARE_BASE}/Procedure",
        headers = get_primary_care_headers(),
        json    = new_procedure
    )
    print(f"HTTP Status : {create_response.status_code}")
    created = create_response.json()
    new_id  = created.get("id")
    if new_id:
        print(f"Created Procedure on Primary Care EHR - ID: {new_id}")
        new_procedure["id"] = new_id

    return new_procedure

def get_primary_care_practitioner_id():
    print(f"\n[Practitioner Lookup] GET /Practitioner?_count=1")
    entries = requests.get(
        f"{PRIMARY_CARE_BASE}/Practitioner",
        headers = get_primary_care_headers(),
        params  = {"_count": 1}
    ).json().get("entry", [])

    if entries:
        r     = entries[0]["resource"]
        pc_id = r.get("id")
        n     = r.get("name", [{}])[0]
        print(f"  Found   : Practitioner/{pc_id} — "
              f"{n.get('given',['?'])[0]} {n.get('family','?')}")
        return f"Practitioner/{pc_id}"

    print(" WARNING: No Practitioner found.")
    return None

def create_procedure_on_primary_care(primary_care_patient_id, practitioner_ref,
                                     openemr_procedure):
    performed_dt = (
        openemr_procedure.get("performedDateTime")
        or openemr_procedure.get("performedPeriod", {}).get("start")
        or openemr_procedure.get("period", {}).get("start")
        or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    )

    status = "completed"

    procedure_payload = {
        "resourceType": "Procedure",
        "text": {
            "status": "generated",
            "div": (
                f'<div xmlns="http://www.w3.org/1999/xhtml">'
                f'Procedure: {PROCEDURE_DISPLAY} — Status: {status} — '
                f'Performed: {performed_dt}</div>'
            )
        },
        "status": status,
        "category": {
            "coding": [
                {
                    "system":  SNOMED_SYSTEM,
                    "code":    "103693007",
                    "display": "Diagnostic procedure"
                }
            ],
            "text": "Diagnostic procedure"
        },
        "code": {
            "coding": [
                {
                    "system":  SNOMED_SYSTEM,
                    "code":    PROCEDURE_CODE,
                    "display": PROCEDURE_DISPLAY
                }
            ],
            "text": PROCEDURE_DISPLAY
        },
        "subject": {
            "reference": f"Patient/{primary_care_patient_id}"
        },
        "performedDateTime": performed_dt,
        "performer": [
            {
                "actor": {
                    "reference": practitioner_ref
                }
            }
        ] if practitioner_ref else [],
        "bodySite": [
            {
                "coding": [
                    {
                        "system":  SNOMED_SYSTEM,
                        "code":    PROCEDURE_SITE_CODE,
                        "display": PROCEDURE_SITE_DISPLAY
                    }
                ],
                "text": PROCEDURE_SITE_DISPLAY
            }
        ],
        "reasonCode": [
            {
                "coding": [
                    {
                        "system":  SNOMED_SYSTEM,
                        "code":    "13645005",
                        "display": "Chronic obstructive lung disease"
                    }
                ],
                "text": "Chronic obstructive lung disease"
            }
        ],
        "followUp": [
            {
                "text": "Routine follow-up in 2 weeks"
            }
        ],
        "note": [
            {
                "text": (
                    "Plain X-ray of chest performed. "
                    "No abnormalities detected. "
                    "Procedure completed successfully."
                )
            }
        ]
    }


    print("Creating Procedure - Primary Care EHR")

    print(f"  Subject      : Patient/{primary_care_patient_id}")
    print(f"  Performer    : {practitioner_ref}")
    print(f"  Procedure    : SNOMED {PROCEDURE_CODE} — {PROCEDURE_DISPLAY}")
    print(f"  Procedure Site : SNOMED {PROCEDURE_SITE_CODE} — {PROCEDURE_SITE_DISPLAY}")
    print(f"  Status       : {status}")
    print(f"  Performed    : {performed_dt}")
    print(f"  Follow Up    : Routine follow-up in 2 weeks")
    print(f"  Note         : Plain X-ray of chest performed. No abnormalities detected. Procedure completed successfully.")

    print("\n Procedure JSON Payload")
    print(json.dumps(procedure_payload, indent=4))

    response = requests.post(
        url     = f"{PRIMARY_CARE_BASE}/Procedure",
        headers = get_primary_care_headers(),
        json    = procedure_payload
    )
    print(f"HTTP Status  : {response.status_code}")
    procedure_id = response.json().get("id")
    print(f"Success      : New Procedure ID → {procedure_id}")

    with open(data_dir / "task4_procedure.json", "w") as f:
        json.dump(procedure_payload, f, indent=4)
    print(f"  Cached     : data/task4_procedure.json")

    return procedure_id, procedure_payload

if __name__ == "__main__":
    print("PROCEDURE PIPELINE")
    print("Flow: OpenEMR (encounters) → Primary Care EHR (POST)")

    patients = search_patient()
    selected_patient   = None
    openemr_patient_id = None
    for entry in patients:
        candidate = entry["resource"]
        if candidate.get("deceasedBoolean") or candidate.get("deceasedDateTime"):
            continue
        selected_patient   = candidate
        openemr_patient_id = candidate["id"]
        break

    if not selected_patient:
        print("\nNo living candidate found for David Abshire.")
        exit(1)

    p_name   = selected_patient.get("name", [{}])[0]
    p_given  = p_name.get("given", [""])[0]
    p_family = p_name.get("family", "")
    print(f"\nSelected: {p_given} {p_family} (OpenEMR ID: {openemr_patient_id})")
    encounter_entries = get_patient_encounters(openemr_patient_id)
    openemr_procedure = select_procedure_from_encounters(
        encounter_entries, openemr_patient_id
    )

    if openemr_procedure:
        print(f"\nSource Encounter ID : {openemr_procedure.get('id', 'unknown')}")
        print(f"Performed / Start   : "
              f"{openemr_procedure.get('performedDateTime') or openemr_procedure.get('period', {}).get('start', 'unknown')}")
    else:
        print("\nWARNING: No source procedure could be retrieved or created.")
        openemr_procedure = {}

    print("Inheriting Primary Care Patient ID (from Task 1)")
    with open(data_dir / "task1_patient_id.json", "r") as f:
        primary_care_patient_id = json.load(f).get("patient_id")
    print(f"Reusing existing Primary Care Patient ID: {primary_care_patient_id} (from Task 1)")

    practitioner_ref = get_primary_care_practitioner_id()

    procedure_id, _ = create_procedure_on_primary_care(
        primary_care_patient_id = primary_care_patient_id,
        practitioner_ref        = practitioner_ref,
        openemr_procedure       = openemr_procedure
    )

    print("EXECUTION SUMMARY")
    print(f"\nSOURCE (OpenEMR)")
    print(f"    Patient        : {p_given} {p_family}  (ID: {openemr_patient_id})")
    print(f"    Procedure Code : SNOMED {PROCEDURE_CODE} - {PROCEDURE_DISPLAY}")
    print(f"    Procedure Site : SNOMED {PROCEDURE_SITE_CODE} - {PROCEDURE_SITE_DISPLAY}")

    print(f"\nDESTINATION (Primary Care EHR)")
    print(f"    Patient ID     : {primary_care_patient_id}  (Reused from Task 1)")
    print(f"    Performer      : {practitioner_ref}")
    print(f"    Procedure ID   : {procedure_id}")
    print(f"    Reason Code    : SNOMED 13645005 - Chronic obstructive lung disease")
    print(f"    Follow Up      : Routine follow-up in 2 weeks")
    print(f"    Note           : Plain X-ray of chest performed. No abnormalities detected. Procedure completed successfully.")
    print("Pipeline complete.")