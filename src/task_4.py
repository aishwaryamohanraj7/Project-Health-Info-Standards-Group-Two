import json
import requests
from datetime import datetime, timezone
from pathlib import Path

# ============================================================
# ENDPOINT CONFIGURATIONS
# ============================================================
OPENEMR_BASE      = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
PRIMARY_CARE_BASE = "http://159.203.105.138:8080/fhir"

# ============================================================
# TARGET PATIENT CRITERIA  (David Abshire — same as Tasks 1–3)
# ============================================================
SEARCH_GENDER = "male"
SEARCH_GIVEN  = "David"
SEARCH_FAMILY = "Abshire"

# ============================================================
# SNOMED & LOINC CODE CONSTANTS
# ============================================================
SNOMED_SYSTEM = "http://snomed.info/sct"
LOINC_SYSTEM  = "http://loinc.org"

# Procedure code: Spirometry (SNOMED 127783003)
PROCEDURE_CODE    = "127783003"
PROCEDURE_DISPLAY = "Spirometry"

# Body site: Lung structure (SNOMED 39607008)
BODY_SITE_CODE    = "39607008"
BODY_SITE_DISPLAY = "Lung structure"

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

def get_primary_care_headers():
    return {
        "Content-Type": "application/fhir+json",
        "Accept":        "application/fhir+json"
    }


# ────────────────────────────────────────────────────────────
# PHASE 1 — PATIENT DISCOVERY (OpenEMR)
# ────────────────────────────────────────────────────────────
def search_patient():
    """
    Queries OpenEMR to locate David Abshire by name and gender.
    Returns: A list of matching Patient entries from the FHIR Bundle.
    """
    url    = f"{OPENEMR_BASE}/Patient"
    params = {"given": SEARCH_GIVEN, "family": SEARCH_FAMILY, "gender": SEARCH_GENDER}

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
# PHASE 2 — CHECK FOR EXISTING PROCEDURE IN OPENEMR
# ────────────────────────────────────────────────────────────
def get_procedure_from_openemr(openemr_patient_id):
    """
    Queries OpenEMR's Procedure endpoint for the given patient.

    Strategy:
      1. Broad fetch — retrieve ALL procedures for the patient and
         display the complete list so every record is visible.
      2. Preferred match — scan the list for a COPD-related or
         pulmonary procedure (keywords: 'pulmonary', 'spirometry',
         'lung', 'respiratory', 'bronch', 'copd').
      3. Fallback — if no keyword match, use the first procedure
         returned (most recent by server ordering).
      4. Create — if OpenEMR returns no procedures at all, create a
         Spirometry record so the pipeline always has a source.

    Returns: The selected Procedure resource dict, or None.
    """
    print(f"\n{'='*60}")
    print("[Phase 2] Fetching All Procedures from OpenEMR")
    print(f"{'='*60}")

    # ── Step 1: Broad fetch — all encounters for this patient ────────────
    print(f"\n  GET /Encounter?patient={openemr_patient_id}&_count=50")
    response = requests.get(
        f"{OPENEMR_BASE}/Encounter",
        headers = get_openemr_headers(),
        params  = {"patient": openemr_patient_id, "_count": 50}
    )
    entries = response.json().get("entry", [])
    print(f"  Total encounters found : {len(entries)}\n")

    if entries:
        # ── Step 2: Display every encounter found ────────────────────────
        # Encounter descriptions live in type[].coding[] (not code),
        # mirroring the pattern used in Phase 2 of the reference pipeline
        # (get_patient_conditions) which reads codings[] then falls back
        # to code.text.  We apply the same two-level fallback here.
        def extract_encounter_display(r):
            """
            Pull the best available description from an Encounter resource.
            Checks fields in priority order:
              1. type[].coding[].display  — structured encounter type
              2. type[].text              — plain-text encounter type
              3. reasonCode[].coding[].display — clinical reason for visit
              4. reasonCode[].text        — plain-text reason
              5. serviceType.coding[].display  — department / service
              6. class.display            — encounter class (ambulatory etc.)
            Also collects a separate reason string to show alongside the type.
            """
            code_val = "—"
            type_display = "—"

            # 1 & 2: type
            for t in r.get("type", []):
                for coding in t.get("coding", []):
                    if coding.get("display"):
                        code_val     = coding.get("code", "—")
                        type_display = coding["display"]
                        break
                if type_display != "—":
                    break
                if t.get("text"):
                    type_display = t["text"]
                    break

            # 3 & 4: reasonCode — append to give context beyond "check up"
            reason_display = ""
            for rc in r.get("reasonCode", []):
                for coding in rc.get("coding", []):
                    if coding.get("display"):
                        reason_display = coding["display"]
                        break
                if not reason_display and rc.get("text"):
                    reason_display = rc["text"]
                if reason_display:
                    break

            # 5: serviceType
            if type_display == "—":
                for coding in r.get("serviceType", {}).get("coding", []):
                    if coding.get("display"):
                        type_display = coding["display"]
                        break

            # 6: class fallback
            if type_display == "—":
                cls = r.get("class", {})
                type_display = cls.get("display", "—")
                code_val     = cls.get("code", "—")

            # Combine type + reason so each row carries the full picture
            full_display = (
                f"{type_display} | Reason: {reason_display}"
                if reason_display else type_display
            )
            return code_val, full_display

        # Widen Description column to show type + reason comfortably
        print(f"  {'#':<4} {'ID':<36} {'Code':<14} {'Description / Reason':<60} {'Status':<12} {'Period Start'}")
        print(f"  {'-'*4} {'-'*36} {'-'*14} {'-'*60} {'-'*12} {'-'*20}")
        for i, entry in enumerate(entries):
            r                  = entry["resource"]
            code_val, display  = extract_encounter_display(r)
            status             = r.get("status", "—")
            period_start       = r.get("period", {}).get("start", "—")
            print(f"  [{i:<2}] {r.get('id','—'):<36} {code_val:<14} {display[:59]:<60} {status:<12} {period_start}")

        # ── Step 3: Preferred match — COPD / pulmonary keyword scan ─────
        KEYWORDS = ("pulmonary", "spirometry", "lung", "respiratory",
                    "bronch", "copd", "obstructive")
        preferred = None
        for entry in entries:
            r                 = entry["resource"]
            _, display        = extract_encounter_display(r)
            if any(kw in display.lower() for kw in KEYWORDS):
                preferred = r
                break

        if preferred:
            _, disp = extract_encounter_display(preferred)
            print(f"\n  Preferred match (keyword) : ID {preferred.get('id')} — {disp}")
            return preferred

        # ── Step 4: Fallback — use first entry ───────────────────────────
        fallback      = entries[0]["resource"]
        _, disp       = extract_encounter_display(fallback)
        print(f"\n  No keyword match found. Using first record : "
              f"ID {fallback.get('id')} — {disp}")
        return fallback

    # ── No procedures at all — create one in OpenEMR ─────────────────────
    print(f"  No Procedure resources found in OpenEMR for patient {openemr_patient_id}.")
    print(f"  Creating a Spirometry Procedure record in OpenEMR...")

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
                        "code":    BODY_SITE_CODE,
                        "display": BODY_SITE_DISPLAY
                    }
                ]
            }
        ]
    }

    create_response = requests.post(
        f"{OPENEMR_BASE}/Procedure",
        headers = get_openemr_headers(),
        json    = new_procedure
    )
    print(f"  HTTP Status : {create_response.status_code}")
    created = create_response.json()
    new_id  = created.get("id")
    if new_id:
        print(f"  Created Procedure in OpenEMR — ID: {new_id}")
        new_procedure["id"] = new_id
        return new_procedure

    print("  WARNING: OpenEMR did not return an ID — proceeding with local payload.")
    return new_procedure


# ────────────────────────────────────────────────────────────
# PHASE 3 — RESOLVE PRIMARY CARE PATIENT ID
# ────────────────────────────────────────────────────────────
def get_primary_care_patient_id(openemr_patient_id):
    """
    Looks up the patient on the Primary Care server by their OpenEMR ID
    used as an MR identifier.  Falls back to re-posting the cached
    patient.json if no live match is found.

    Returns: Primary Care Patient ID string, or None.
    """
    print(f"\n{'='*60}")
    print("[Phase 3] Resolving Primary Care EHR Patient ID")
    print(f"{'='*60}")
    print(f"  Searching by MR identifier: {openemr_patient_id}")

    entries = requests.get(
        f"{PRIMARY_CARE_BASE}/Patient",
        headers = get_primary_care_headers(),
        params  = {"identifier": openemr_patient_id}
    ).json().get("entry", [])

    if entries:
        pc_id = entries[0]["resource"].get("id")
        print(f"  Match found — Primary Care Patient ID: {pc_id}")
        return pc_id

    cache_path = data_dir / "patient.json"
    if cache_path.exists():
        print(f"  No live match. Re-posting cached patient from: {cache_path}")
        with open(cache_path) as f:
            cached = json.load(f)
        pc_id = requests.post(
            f"{PRIMARY_CARE_BASE}/Patient",
            headers = get_primary_care_headers(),
            json    = cached
        ).json().get("id")
        print(f"  Re-posted. Primary Care Patient ID: {pc_id}")
        return pc_id

    print("  ERROR: Could not resolve Primary Care Patient ID.")
    return None


def get_primary_care_practitioner_id():
    """
    Fetches the first available Practitioner from the Primary Care server.
    Returns: A reference string like 'Practitioner/{id}', or None.
    """
    print(f"\n  [Practitioner Lookup] GET /Practitioner?_count=1")
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

    print("  WARNING: No Practitioner found.")
    return None


# ────────────────────────────────────────────────────────────
# PHASE 4 — BUILD & POST PROCEDURE TO PRIMARY CARE EHR
# ────────────────────────────────────────────────────────────
def create_procedure_on_primary_care(primary_care_patient_id, practitioner_ref,
                                     openemr_procedure):
    """
    Constructs a FHIR R4 Procedure resource derived from the OpenEMR source
    and POSTs it to the Primary Care EHR server.

    Fields sourced at runtime:
      • subject        — resolved Primary Care patient ID
      • performer      — resolved from /Practitioner query
      • performedDateTime — carried from OpenEMR record (or current time)
      • code / bodySite  — SNOMED codes for Spirometry / Lung structure
    """
    # Carry over performedDateTime from OpenEMR source if available
    performed_dt = (
        openemr_procedure.get("performedDateTime")
        or openemr_procedure.get("performedPeriod", {}).get("start")
        or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    )

    # Carry over status from source, default to "completed"
    status = openemr_procedure.get("status", "completed")

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
        "subject":           {"reference": f"Patient/{primary_care_patient_id}"},
        "performedDateTime": performed_dt,
        "performer": (
            [
                {
                    "actor": {"reference": practitioner_ref}
                }
            ]
            if practitioner_ref else []
        ),
        "bodySite": [
            {
                "coding": [
                    {
                        "system":  SNOMED_SYSTEM,
                        "code":    BODY_SITE_CODE,
                        "display": BODY_SITE_DISPLAY
                    }
                ],
                "text": BODY_SITE_DISPLAY
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
        "note": [
            {
                "text": (
                    "Spirometry performed to assess pulmonary function. "
                    "Results forwarded to Primary Care EHR."
                )
            }
        ]
    }

    print(f"\n{'='*60}")
    print("[Phase 4] Creating Procedure — Primary Care EHR")
    print(f"{'='*60}")
    print(f"  Subject      : Patient/{primary_care_patient_id}")
    print(f"  Performer    : {practitioner_ref}")
    print(f"  Procedure    : SNOMED {PROCEDURE_CODE} — {PROCEDURE_DISPLAY}")
    print(f"  Body Site    : SNOMED {BODY_SITE_CODE} — {BODY_SITE_DISPLAY}")
    print(f"  Status       : {status}")
    print(f"  Performed    : {performed_dt}")

    print("\n  [=== Procedure JSON Payload ===]")
    print(json.dumps(procedure_payload, indent=4))
    print("  [==============================]\n")

    response = requests.post(
        url     = f"{PRIMARY_CARE_BASE}/Procedure",
        headers = get_primary_care_headers(),
        json    = procedure_payload
    )
    print(f"  HTTP Status  : {response.status_code}")
    procedure_id = response.json().get("id")
    print(f"  Success      : New Procedure ID → {procedure_id}")

    with open(data_dir / "task4_procedure.json", "w") as f:
        json.dump(procedure_payload, f, indent=4)
    print(f"  Cached       : data/task4_procedure.json")

    return procedure_id, procedure_payload


# ============================================================
# MAIN PIPELINE
# ============================================================
if __name__ == "__main__":

    print("\n" + "="*60)
    print("  TASK 4 — PROCEDURE PIPELINE")
    print("  Flow: OpenEMR (check/create) → Primary Care EHR (POST)")
    print("="*60)

    # ── Phase 1: Locate David Abshire ──────────────────────────────────
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
        print("\n[FATAL] No living candidate found for David Abshire.")
        exit(1)

    p_name   = selected_patient.get("name", [{}])[0]
    p_given  = p_name.get("given", [""])[0]
    p_family = p_name.get("family", "")
    print(f"\n  Selected: {p_given} {p_family} (OpenEMR ID: {openemr_patient_id})")

    # ── Patient Data Dump ────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  PATIENT DATA DUMP — Full OpenEMR Resource")
    print(f"{'='*60}")
    print(json.dumps(selected_patient, indent=4))
    print(f"{'='*60}")

    # ── Phase 2: Check / create Procedure in OpenEMR ────────────────────
    openemr_procedure = get_procedure_from_openemr(openemr_patient_id)

    if openemr_procedure:
        src_code = openemr_procedure.get("code", {}).get("coding", [{}])[0]
        print(f"\n  Source Procedure : {src_code.get('display','?')} "
              f"(SNOMED {src_code.get('code','?')})")
        print(f"  Performed        : {openemr_procedure.get('performedDateTime','unknown')}")
    else:
        print("\n  WARNING: OpenEMR Procedure could not be retrieved or created.")
        print("  Proceeding with default Spirometry values.")
        openemr_procedure = {}

    # ── Phase 3: Resolve Primary Care Patient + Practitioner ────────────
    primary_care_patient_id = get_primary_care_patient_id(openemr_patient_id)
    if not primary_care_patient_id:
        print("\n[FATAL] Cannot resolve Primary Care Patient ID.")
        exit(1)

    practitioner_ref = get_primary_care_practitioner_id()

    # ── Phase 4: Build and POST the Procedure ───────────────────────────
    procedure_id, _ = create_procedure_on_primary_care(
        primary_care_patient_id = primary_care_patient_id,
        practitioner_ref        = practitioner_ref,
        openemr_procedure       = openemr_procedure
    )

    # ── Final Summary ────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("           TASK 4 — EXECUTION SUMMARY")
    print(f"{'='*60}")
    print(f"\n  SOURCE (OpenEMR)")
    print(f"    Patient        : {p_given} {p_family}  (ID: {openemr_patient_id})")
    print(f"    Procedure Code : SNOMED {PROCEDURE_CODE} — {PROCEDURE_DISPLAY}")
    print(f"    Body Site      : SNOMED {BODY_SITE_CODE} — {BODY_SITE_DISPLAY}")

    print(f"\n  DESTINATION (Primary Care EHR)")
    print(f"    Patient ID     : {primary_care_patient_id}")
    print(f"    Performer      : {practitioner_ref}")
    print(f"    Procedure ID   : {procedure_id}")
    print(f"    Reason Code    : SNOMED 13645005 — Chronic obstructive lung disease")
    print(f"\n{'='*60}")
    print("  Pipeline complete.")
    print(f"{'='*60}\n")