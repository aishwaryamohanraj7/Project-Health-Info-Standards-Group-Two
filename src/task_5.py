import json
import requests
from pathlib import Path
from datetime import datetime
from hl7apy.core import Message

# ENDPOINT CONFIGURATIONS

OPENEMR_BASE  = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
HERMES_BASE   = "http://159.203.121.13:8080/v1/snomed"

# TARGET PATIENT CRITERIA (same as Task 1 — David Abshire)
SEARCH_GENDER = "male"
SEARCH_GIVEN  = "David"
SEARCH_FAMILY = "Abshire"

# ============================================================
# LOCAL STORAGE
# ============================================================
data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)


# ────────────────────────────────────────────────────────────
# SECURITY & AUTHENTICATION
# ────────────────────────────────────────────────────────────
def get_access_token():
    with open(data_dir / "access_token.json", "r") as f:
        return json.load(f).get("access_token")

def get_openemr_headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Accept": "application/json"
    }


# ────────────────────────────────────────────────────────────
# PHASE 1 — PATIENT DISCOVERY (same logic as Task 1)
# ────────────────────────────────────────────────────────────
def search_patient():
    url    = f"{OPENEMR_BASE}/Patient"
    params = {
        "given":  SEARCH_GIVEN,
        "family": SEARCH_FAMILY,
        "gender": SEARCH_GENDER
    }

    print(f"\n{'='*60}")
    print("[Phase 1] Patient Discovery — OpenEMR")
    print(f"{'='*60}")
    print(f"  Request : GET /Patient?given={SEARCH_GIVEN}&family={SEARCH_FAMILY}&gender={SEARCH_GENDER}")

    response = requests.get(url=url, headers=get_openemr_headers(), params=params)
    entries  = response.json().get("entry", [])

    print(f"  Result  : {len(entries)} candidate(s) returned.\n")
    for i, e in enumerate(entries[:10]):
        r = e["resource"]
        n = r.get("name", [{}])[0]
        print(f"  [{i}] ID: {r.get('id')} | {n.get('given',[''])[0]} {n.get('family','')} | "
              f"Gender: {r.get('gender')} | DOB: {r.get('birthDate')} | "
              f"Deceased: {r.get('deceasedBoolean') or r.get('deceasedDateTime')}")
    return entries


# ────────────────────────────────────────────────────────────
# PHASE 2 — CONDITION EXTRACTION (same logic as Task 1)
# ────────────────────────────────────────────────────────────
def get_patient_conditions(patient_id):
    url    = f"{OPENEMR_BASE}/Condition"
    params = {"patient": patient_id}

    print(f"\n{'='*60}")
    print(f"[Phase 2] Condition Extraction — Patient ID: {patient_id}")
    print(f"{'='*60}")

    response = requests.get(url=url, headers=get_openemr_headers(), params=params)
    entries  = response.json().get("entry", [])

    print(f"  Total conditions found: {len(entries)}\n")
    if not entries:
        print("  WARNING: No conditions documented for this patient.")
        return None

    for i, entry in enumerate(entries):
        r          = entry["resource"]
        code_field = r.get("code", {})
        codings    = code_field.get("coding", [])
        if codings:
            display = codings[0].get("display", "unknown")
            system  = codings[0].get("system", "unknown")
        else:
            display = code_field.get("text", "unknown")
            system  = "text-only"
        print(f"  [{i}] Terminology: {display}  |  Code System: {system}")

    return entries


# ────────────────────────────────────────────────────────────
# PHASE 3 — SNOMED TEXT SEARCH (same logic as Task 1)
# ────────────────────────────────────────────────────────────
def search_snomed_by_text(search_term):
    print(f"\n  [Hermes] Text search: '{search_term}'")
    response = requests.get(
        f"{HERMES_BASE}/search",
        params={"s": search_term, "constraint": "<404684003", "maxHits": 1}
    )
    data  = response.json()
    items = data if isinstance(data, list) else data.get("items", [])

    if not items:
        print("  [Hermes] No match found.")
        return None, None

    concept_id     = items[0].get("conceptId") or items[0].get("id")
    preferred_term = items[0].get("preferredTerm") or items[0].get("term", search_term)
    print(f"  [Hermes] Matched concept : {concept_id} | {preferred_term}")

    return concept_id, preferred_term


# ────────────────────────────────────────────────────────────
# PHASE 4 — SNOMED → ICD-10 MAPPING VIA HERMES
# ────────────────────────────────────────────────────────────
def snomed_to_icd(snomed_code):
    """
    Map a SNOMED CT concept to ICD-10 using Hermes cross-map endpoint.
    Reference set 447562003 = ICD-10 complex map reference set.
    Returns: ICD-10 code string or 'UNKNOWN'
    """
    print(f"\n{'='*60}")
    print(f"[Phase 4] SNOMED → ICD-10 Mapping")
    print(f"{'='*60}")
    print(f"  Endpoint : GET /v1/snomed/concepts/{snomed_code}/map/447562003")

    response = requests.get(
        f"{HERMES_BASE}/concepts/{snomed_code}/map/447562003"
    )

    print(f"  HTTP     : {response.status_code}")

    try:
        data = response.json()
        print(f"  Raw map response: {json.dumps(data, indent=4)}")
        if data:
            icd_code = data[0].get("mapTarget", "UNKNOWN")
            print(f"  ICD-10 Code : {icd_code}")
            return icd_code
    except Exception as e:
        print(f"  ERROR parsing map response: {e}")

    return "UNKNOWN"


# ────────────────────────────────────────────────────────────
# PHASE 5 — BUILD HL7 ADT^A01 MESSAGE
# ────────────────────────────────────────────────────────────
def build_hl7_message(patient, snomed_code, snomed_display, icd_code):
    """
    Construct a simplified HL7 v2.5 ADT^A01 message using data
    extracted dynamically from OpenEMR and Hermes.

    Segments included:
      MSH — Message header
      PID — Patient identification (ID, name, DOB, gender, address)
      PV1 — Patient visit information
      DG1 — Diagnosis (ICD-10 mapped from SNOMED)
    """
    # Extract patient fields dynamically
    patient_id  = patient.get("id", "UNKNOWN")
    name        = patient.get("name", [{}])[0]
    given       = name.get("given", ["UNKNOWN"])[0]
    family      = name.get("family", "UNKNOWN")
    gender_fhir = patient.get("gender", "unknown")
    birth_date  = patient.get("birthDate", "19000101").replace("-", "")

    # Address fields
    address     = patient.get("address", [{}])[0]
    street      = address.get("line", ["UNKNOWN"])[0]
    city        = address.get("city", "UNKNOWN")
    state       = address.get("state", "UNKNOWN")
    postal      = address.get("postalCode", "UNKNOWN")

    # Map FHIR gender to HL7 gender code
    gender_map  = {"male": "M", "female": "F", "other": "O", "unknown": "U"}
    gender_hl7  = gender_map.get(gender_fhir, "U")

    # Timestamp
    now         = datetime.now().strftime("%Y%m%d%H%M%S")

    print(f"\n{'='*60}")
    print("[Phase 5] Building HL7 ADT^A01 Message")
    print(f"{'='*60}")
    print(f"  Patient ID    : {patient_id}")
    print(f"  Name          : {given} {family}")
    print(f"  DOB           : {birth_date}")
    print(f"  Gender (HL7)  : {gender_hl7}")
    print(f"  Address       : {street}, {city}, {state} {postal}")
    print(f"  SNOMED        : {snomed_code} | {snomed_display}")
    print(f"  ICD-10        : {icd_code}")

    # ── Build each segment manually (hl7apy-compatible pipe format) ─────
    msh = (
        f"MSH|^~\\&|OpenEMR|LudyHospital|PrimaryCare|System|{now}||"
        f"ADT^A01|MSG{now}|P|2.5"
    )

    pid = (
        f"PID|1||{patient_id}^^^OpenEMR^MR||"
        f"{family}^{given}^^^||"
        f"{birth_date}|{gender_hl7}|||"
        f"{street}^^{city}^{state}^{postal}^USA"
    )

    pv1 = (
        f"PV1|1|O|Clinic^Room1^Bed1|||"
        f"12345^{family}^{given}^^^Dr|"
        f"12345^{family}^{given}^^^Dr||||||||||"
        f"V{now}"
    )

    dg1 = (
        f"DG1|1||{icd_code}^{snomed_display}^I10|"
        f"{snomed_display}|{now}|A"
    )

    obx = (
        f"OBX|1|NM|55284-4^Blood Pressure^LN||120/80|mm[Hg]|"
        f"90-120/60-80||||F|||{now}"
    )

    hl7_message = "\n".join([msh, pid, pv1, obx, dg1])

    return hl7_message


# ────────────────────────────────────────────────────────────
# PHASE 6 — SAVE HL7 MESSAGE TO FILE
# ────────────────────────────────────────────────────────────
def save_hl7(hl7_message):
    output_path = Path(__file__).parent / "hl7_message.txt"
    with open(output_path, "w") as f:
        f.write(hl7_message)
    print(f"\n  HL7 message saved to: {output_path}")
    return output_path


# ============================================================
# MAIN PIPELINE
# ============================================================
if __name__ == "__main__":

    print("\n" + "="*60)
    print("  TASK 5 — HL7 ADT MESSAGE PIPELINE")
    print("  Flow: OpenEMR → Hermes (SNOMED→ICD) → HL7 ADT^A01")
    print("="*60)

    # ── Phase 1: Locate David Abshire (same as Task 1) ────────────────
    patients = search_patient()

    selected_patient   = None
    openemr_patient_id = None
    snomed_code        = None
    snomed_display     = None

    for patient_entry in patients:
        candidate = patient_entry["resource"]

        if candidate.get("deceasedBoolean") or candidate.get("deceasedDateTime"):
            continue

        candidate_id = candidate["id"]
        candidate_name = candidate.get("name", [{}])[0]
        print(f"\n  Evaluating: {candidate_name.get('given', [''])[0]} "
              f"{candidate_name.get('family', '')} (ID: {candidate_id})")

        # ── Phase 2: Pull conditions ───────────────────────────────────
        conds = get_patient_conditions(candidate_id)
        if not conds:
            continue

        # ── Find COPD from condition list (same as Task 1) ────────────
        for entry in conds:
            r       = entry["resource"]
            codings = r.get("code", {}).get("coding", [])
            text    = r.get("code", {}).get("text", "")
            display = codings[0].get("display", "") if codings else ""

            if ("obstructive pulmonary" in text.lower() or
                    "obstructive pulmonary" in display.lower()):

                looked_up_id, looked_up_term = search_snomed_by_text(
                    "Chronic Obstructive Pulmonary Disease"
                )
                if looked_up_id:
                    snomed_code    = str(looked_up_id)
                    snomed_display = looked_up_term
                    break

        if snomed_code:
            selected_patient   = candidate
            openemr_patient_id = candidate_id
            print(f"\n  Selected Condition : {snomed_display} (SNOMED: {snomed_code})")
            break

    if not selected_patient or not snomed_code:
        print("\n[FATAL] Could not locate the specified patient/condition.")
        exit(1)

    # ── Phase 4: Map SNOMED → ICD-10 via Hermes ───────────────────────
    icd_code = snomed_to_icd(snomed_code)

    # ── Phase 5: Build HL7 ADT^A01 message ────────────────────────────
    hl7_message = build_hl7_message(
        patient        = selected_patient,
        snomed_code    = snomed_code,
        snomed_display = snomed_display,
        icd_code       = icd_code
    )

    print(f"\n{'='*60}")
    print("[Phase 5] HL7 ADT^A01 Message Output")
    print(f"{'='*60}")
    print(hl7_message)

    # ── Phase 6: Save to file ─────────────────────────────────────────
    saved_path = save_hl7(hl7_message)

    # ── Final Summary ─────────────────────────────────────────────────
    p_name  = selected_patient.get("name", [{}])[0]
    p_given = p_name.get("given", [""])[0]
    p_family= p_name.get("family", "")

    print(f"\n{'='*60}")
    print("           TASK 5 — EXECUTION SUMMARY")
    print(f"{'='*60}")
    print(f"\n  SOURCE (OpenEMR)")
    print(f"    Patient      : {p_given} {p_family}  (ID: {openemr_patient_id})")
    print(f"    Condition    : {snomed_display}")
    print(f"    SNOMED Code  : {snomed_code}")

    print(f"\n  TERMINOLOGY MAPPING (Hermes)")
    print(f"    SNOMED → ICD : {snomed_code} → {icd_code}")
    print(f"    Map Ref Set  : 447562003 (ICD-10 complex map)")

    print(f"\n  HL7 OUTPUT")
    print(f"    Message Type : ADT^A01")
    print(f"    Segments     : MSH, PID, PV1, DG1")
    print(f"    Saved To     : {saved_path}")
    print(f"\n{'='*60}")
    print("  Pipeline complete.")
    print(f"{'='*60}\n")