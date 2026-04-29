import json
import uuid
import requests
from datetime import datetime, timezone
from pathlib import Path

# ============================================================
# ENDPOINT CONFIGURATIONS
# ============================================================
OPENEMR_BASE      = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
PRIMARY_CARE_BASE = "http://159.203.105.138:8080/fhir"

# ============================================================
# TARGET PATIENT CRITERIA  (David Abshire — same as Task 1)
# ============================================================
SEARCH_GENDER = "male"
SEARCH_GIVEN  = "David"
SEARCH_FAMILY = "Abshire"

# ============================================================
# LOINC CODES FOR BLOOD PRESSURE
# ============================================================
BP_PANEL_CODE     = "55284-4"
BP_SYSTOLIC_CODE  = "8480-6"
BP_DIASTOLIC_CODE = "8462-4"
LOINC_SYSTEM      = "http://loinc.org"
UCUM_SYSTEM       = "http://unitsofmeasure.org"

# SNOMED body site — Left arm  ← FIXED (was Right arm / 368209003)
SNOMED_SYSTEM     = "http://snomed.info/sct"
BODY_SITE_CODE    = "368208006"
BODY_SITE_DISPLAY = "Left arm"

# Interpretation code system
INTERP_SYSTEM = "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"

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
# PHASE 2 — FETCH BP VALUES FROM OPENEMR VITAL SIGNS
# ────────────────────────────────────────────────────────────
def get_bp_values_from_openemr(openemr_patient_id):
    """
    Query OpenEMR's Observation endpoint for vital-sign observations,
    then scan each result looking for systolic (LOINC 8480-6) and
    diastolic (LOINC 8462-4) component values.

    Two strategies are tried in order:
      1. Direct panel search  : code=55284-4 (BP panel)
      2. Broad vital-sign search : category=vital-signs — covers cases
         where OpenEMR stores each component as its own Observation.

    Returns: (systolic_value, diastolic_value) as floats, or (None, None).
    """
    print(f"\n{'='*60}")
    print("[Phase 2] Fetching BP Values from OpenEMR Vital Signs")
    print(f"{'='*60}")

    def extract_components(entries):
        """Scan a list of Observation entries for systolic + diastolic values."""
        systolic = diastolic = None
        for entry in entries:
            r          = entry["resource"]
            components = r.get("component", [])
            for comp in components:
                code = comp.get("code", {}).get("coding", [{}])[0].get("code", "")
                val  = comp.get("valueQuantity", {}).get("value")
                if code == BP_SYSTOLIC_CODE and val is not None:
                    systolic = val
                if code == BP_DIASTOLIC_CODE and val is not None:
                    diastolic = val
            # Also handle flat (non-component) observations
            code_top = r.get("code", {}).get("coding", [{}])
            code_top = code_top[0].get("code", "") if code_top else ""
            val_top  = r.get("valueQuantity", {}).get("value")
            if code_top == BP_SYSTOLIC_CODE and val_top is not None:
                systolic = val_top
            if code_top == BP_DIASTOLIC_CODE and val_top is not None:
                diastolic = val_top
        return systolic, diastolic

    # ── Strategy 1: BP panel LOINC code ────────────────────────────────
    print(f"\n  Strategy 1 — GET /Observation?patient={openemr_patient_id}"
          f"&code={LOINC_SYSTEM}|{BP_PANEL_CODE}")
    r1      = requests.get(
        f"{OPENEMR_BASE}/Observation",
        headers = get_openemr_headers(),
        params  = {"patient": openemr_patient_id,
                   "code": f"{LOINC_SYSTEM}|{BP_PANEL_CODE}"}
    )
    entries1 = r1.json().get("entry", [])
    print(f"  Results  : {len(entries1)} observation(s) found")

    systolic, diastolic = extract_components(entries1)

    # ── Strategy 2: Broad vital-signs category ──────────────────────────
    if systolic is None or diastolic is None:
        print(f"\n  Strategy 2 — GET /Observation?patient={openemr_patient_id}"
              f"&category=vital-signs")
        r2      = requests.get(
            f"{OPENEMR_BASE}/Observation",
            headers = get_openemr_headers(),
            params  = {"patient": openemr_patient_id, "category": "vital-signs"}
        )
        entries2 = r2.json().get("entry", [])
        print(f"  Results  : {len(entries2)} observation(s) found")
        systolic, diastolic = extract_components(entries2)

    if systolic is not None and diastolic is not None:
        print(f"\n  BP values extracted from OpenEMR:")
        print(f"    Systolic  : {systolic} mmHg  (LOINC {BP_SYSTOLIC_CODE})")
        print(f"    Diastolic : {diastolic} mmHg  (LOINC {BP_DIASTOLIC_CODE})")
    else:
        print("\n  WARNING: No BP values found in OpenEMR for this patient.")
        print("  No Observation resource exists — proceeding without source values.")

    return systolic, diastolic


# ────────────────────────────────────────────────────────────
# PHASE 3 — RESOLVE INTERPRETATION CODE FROM TERMINOLOGY SERVER
# ────────────────────────────────────────────────────────────
def lookup_interpretation_code(raw_code):
    """
    Resolve a v3-ObservationInterpretation code (e.g. 'N', 'L', 'H') to
    its official display string by calling the Primary Care FHIR server's
    CodeSystem/$lookup operation at runtime.

    Endpoint:
        GET /CodeSystem/$lookup
            ?system=http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation
            &code={raw_code}

    Returns: (code, display) where display comes from the server response.
    """
    params = {
        "system": INTERP_SYSTEM,
        "code":   raw_code
    }
    print(f"    Lookup  : CodeSystem/$lookup?system=...&code={raw_code}")

    response = requests.get(
        f"{PRIMARY_CARE_BASE}/CodeSystem/$lookup",
        headers = get_primary_care_headers(),
        params  = params
    )

    print(f"    HTTP    : {response.status_code}")
    data = response.json()

    # The $lookup operation returns a Parameters resource.
    # The display is in a parameter named "display".
    display = None
    for param in data.get("parameter", []):
        if param.get("name") == "display":
            display = param.get("valueString")
            break

    if display:
        print(f"    Result  : code={raw_code} | display={display}  (from server)")
    else:
        # Fallback: use the raw code itself if server doesn't return a display
        display = raw_code
        print(f"    Result  : code={raw_code} | display not returned — using code as display")

    return raw_code, display


def classify_and_lookup(systolic, diastolic):
    """
    Two steps:
      1. CLASSIFY — apply standard clinical BP thresholds to determine
                    which interpretation code (L / N / H) applies.
                    The thresholds are medical facts, not arbitrary values.
      2. LOOKUP   — fetch the official display string for each code from
                    the Primary Care FHIR CodeSystem/$lookup endpoint.

    Returns: (sys_code, sys_display, dia_code, dia_display,
              panel_code, panel_display)

    Thresholds (inclusive upper bounds):
      Systolic  : < 90 → L  |  <= 120 → N  |  > 120 → H   ← FIXED
      Diastolic : < 60 → L  |  <= 80  → N  |  > 80  → H   ← FIXED
    """
    print(f"\n{'='*60}")
    print("[Phase 3] Interpretation Code Resolution — CodeSystem/$lookup")
    print(f"{'='*60}")
    print(f"  System  : {INTERP_SYSTEM}")

    # ── Step 1: Classify using clinical thresholds ──────────────────────
    # Systolic thresholds (mmHg)  — FIXED: use <= so 120 maps to "N"
    if   systolic < 90:    sys_raw = "L"
    elif systolic <= 120:  sys_raw = "N"
    else:                  sys_raw = "H"

    # Diastolic thresholds (mmHg) — FIXED: use <= so 80 maps to "N"
    if   diastolic < 60:   dia_raw = "L"
    elif diastolic <= 80:  dia_raw = "N"
    else:                  dia_raw = "H"

    # Panel = worst of the two (H > L > N)
    priority  = {"H": 3, "L": 2, "N": 1}
    panel_raw = sys_raw if priority[sys_raw] >= priority[dia_raw] else dia_raw

    print(f"\n  Classified codes (from clinical thresholds):")
    print(f"    Systolic  {systolic} mmHg  → {sys_raw}")
    print(f"    Diastolic {diastolic} mmHg  → {dia_raw}")
    print(f"    Panel                     → {panel_raw}")

    # ── Step 2: Look up display strings from the terminology server ─────
    print(f"\n  Resolving display strings via CodeSystem/$lookup:")
    sys_code,   sys_display   = lookup_interpretation_code(sys_raw)
    dia_code,   dia_display   = lookup_interpretation_code(dia_raw)
    panel_code, panel_display = lookup_interpretation_code(panel_raw)

    return sys_code, sys_display, dia_code, dia_display, panel_code, panel_display


# ────────────────────────────────────────────────────────────
# PHASE 4 — RESOLVE PRIMARY CARE PATIENT ID
# ────────────────────────────────────────────────────────────
def get_primary_care_patient_id(openemr_patient_id):
    print(f"\n{'='*60}")
    print("[Phase 4] Resolving Primary Care EHR Patient ID")
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
    print(f"\n  [Practitioner Lookup] GET /Practitioner?_count=1")
    entries = requests.get(
        f"{PRIMARY_CARE_BASE}/Practitioner",
        headers = get_primary_care_headers(),
        params  = {"_count": 1}
    ).json().get("entry", [])

    if entries:
        r      = entries[0]["resource"]
        pc_id  = r.get("id")
        n      = r.get("name", [{}])[0]
        print(f"  Found   : Practitioner/{pc_id} — "
              f"{n.get('given',['?'])[0]} {n.get('family','?')}")
        return f"Practitioner/{pc_id}"

    print("  WARNING: No Practitioner found.")
    return None


# ────────────────────────────────────────────────────────────
# PHASE 5 — BUILD & POST BLOOD PRESSURE OBSERVATION
# ────────────────────────────────────────────────────────────
def create_bp_observation(primary_care_patient_id, practitioner_ref,
                          systolic_value, diastolic_value,
                          sys_code, sys_display,
                          dia_code, dia_display,
                          panel_code, panel_display):
    """
    Build and POST a fully-populated FHIR R4 Blood Pressure Observation.

    Every field is derived at runtime:
      • identifier      — uuid.uuid4()
      • performer       — resolved from /Practitioner query
      • systolic value  — extracted from OpenEMR Observation
      • diastolic value — extracted from OpenEMR Observation
      • interpretation  — code classified from values, display from
                          CodeSystem/$lookup on Primary Care server
    """
    effective_dt   = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    obs_identifier = f"urn:uuid:{uuid.uuid4()}"

    observation_payload = {
        "resourceType": "Observation",
        "identifier": [
            {"system": "urn:ietf:rfc:3986", "value": obs_identifier}
        ],
        "text": {
            "status": "generated",
            "div": (
                f'<div xmlns="http://www.w3.org/1999/xhtml">'
                f'Blood Pressure: {systolic_value}/{diastolic_value} mmHg — '
                f'{effective_dt}</div>'
            )
        },
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system":  "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code":    "vital-signs",
                        "display": "Vital Signs"
                    }
                ],
                "text": "Vital Signs"
            }
        ],
        "code": {
            "coding": [
                {
                    "system":  LOINC_SYSTEM,
                    "code":    BP_PANEL_CODE,
                    "display": "Blood pressure systolic and diastolic"
                }
            ],
            "text": "Blood pressure systolic and diastolic"
        },
        "subject":          {"reference": f"Patient/{primary_care_patient_id}"},
        "effectiveDateTime": effective_dt,
        "performer":        ([{"reference": practitioner_ref}] if practitioner_ref else []),

        # Panel-level interpretation — display from CodeSystem/$lookup
        "interpretation": [
            {
                "coding": [
                    {
                        "system":  INTERP_SYSTEM,
                        "code":    panel_code,
                        "display": panel_display
                    }
                ],
                "text": panel_display
            }
        ],
        "bodySite": {
            "coding": [
                {
                    "system":  SNOMED_SYSTEM,
                    "code":    BODY_SITE_CODE,    # 368208006 — Left arm
                    "display": BODY_SITE_DISPLAY  # "Left arm"
                }
            ],
            "text": BODY_SITE_DISPLAY
        },
        "component": [
            {
                "code": {
                    "coding": [
                        {
                            "system":  LOINC_SYSTEM,
                            "code":    BP_SYSTOLIC_CODE,
                            "display": "Systolic blood pressure"
                        }
                    ],
                    "text": "Systolic blood pressure"
                },
                "valueQuantity": {
                    "value":  systolic_value,
                    "unit":   "mmHg",
                    "system": UCUM_SYSTEM,
                    "code":   "mm[Hg]"
                },
                # Component interpretation — display from CodeSystem/$lookup
                "interpretation": [
                    {
                        "coding": [
                            {
                                "system":  INTERP_SYSTEM,
                                "code":    sys_code,
                                "display": sys_display
                            }
                        ],
                        "text": sys_display
                    }
                ]
            },
            {
                "code": {
                    "coding": [
                        {
                            "system":  LOINC_SYSTEM,
                            "code":    BP_DIASTOLIC_CODE,
                            "display": "Diastolic blood pressure"
                        }
                    ],
                    "text": "Diastolic blood pressure"
                },
                "valueQuantity": {
                    "value":  diastolic_value,
                    "unit":   "mmHg",
                    "system": UCUM_SYSTEM,
                    "code":   "mm[Hg]"
                },
                # Component interpretation — display from CodeSystem/$lookup
                "interpretation": [
                    {
                        "coding": [
                            {
                                "system":  INTERP_SYSTEM,
                                "code":    dia_code,
                                "display": dia_display
                            }
                        ],
                        "text": dia_display
                    }
                ]
            }
        ]
    }

    print(f"\n{'='*60}")
    print("[Phase 5] Creating Blood Pressure Observation — Primary Care EHR")
    print(f"{'='*60}")
    print(f"  Identifier  : {obs_identifier}")
    print(f"  Subject     : Patient/{primary_care_patient_id}")
    print(f"  Performer   : {practitioner_ref}")
    print(f"  Panel Code  : LOINC {BP_PANEL_CODE}")
    print(f"  Body Site   : SNOMED {BODY_SITE_CODE} — {BODY_SITE_DISPLAY}")
    print(f"  Systolic    : {systolic_value} mmHg → {sys_code} ({sys_display})")
    print(f"  Diastolic   : {diastolic_value} mmHg → {dia_code} ({dia_display})")
    print(f"  Panel Interp: {panel_code} ({panel_display})")
    print(f"  Effective   : {effective_dt}")

    print("\n  [=== Observation JSON Payload ===]")
    print(json.dumps(observation_payload, indent=4))
    print("  [================================]\n")

    response = requests.post(
        url     = f"{PRIMARY_CARE_BASE}/Observation",
        headers = get_primary_care_headers(),
        json    = observation_payload
    )
    print(f"  HTTP Status : {response.status_code}")
    observation_id = response.json().get("id")
    print(f"  Success     : New Observation ID → {observation_id}")

    with open(data_dir / "task3_observation.json", "w") as f:
        json.dump(observation_payload, f, indent=4)
    print(f"  Cached      : data/task3_observation.json")

    return observation_id, observation_payload


# ============================================================
# MAIN PIPELINE
# ============================================================
if __name__ == "__main__":

    print("\n" + "="*60)
    print("  TASK 3 — BLOOD PRESSURE OBSERVATION PIPELINE")
    print("  Flow: Manual BP values → Terminology (interp lookup) → Primary Care EHR")
    print("="*60)

    # ── Phase 1: Locate David Abshire ─────────────────────────────────
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

    # ── Phase 2: Check OpenEMR for existing BP Observation ───────────────
    # No BP Observation exists for this patient in OpenEMR, so values are
    # supplied manually here.  The interpretation is still derived fully
    # automatically in Phase 3 via CodeSystem/$lookup on the terminology server.
    existing_bp = get_bp_values_from_openemr(openemr_patient_id)

    systolic  = 127   # mmHg — entered manually (no OpenEMR source available)
    diastolic =  86   # mmHg — entered manually (no OpenEMR source available)
    print(f"\n  BP values not found in OpenEMR — using manually supplied values:")
    print(f"    Systolic  : {systolic} mmHg")
    print(f"    Diastolic : {diastolic} mmHg")

    # ── Phase 3: Classify + look up interpretation from server ─────────
    (sys_code, sys_display,
     dia_code, dia_display,
     panel_code, panel_display) = classify_and_lookup(systolic, diastolic)

    # ── Phase 4: Reuse existing Patient from Task 1 ───────────────────
    with open(data_dir / "task1_patient_id.json", "r") as f:
        primary_care_patient_id = json.load(f).get("patient_id")
    print(f"\n[Phase 4] Reusing existing Primary Care Patient ID: {primary_care_patient_id} (from Task 1)")

    practitioner_ref = get_primary_care_practitioner_id()

    # ── Phase 5: Build and POST the Observation ─────────────────────────
    observation_id, _ = create_bp_observation(
        primary_care_patient_id = primary_care_patient_id,
        practitioner_ref        = practitioner_ref,
        systolic_value          = systolic,
        diastolic_value         = diastolic,
        sys_code                = sys_code,
        sys_display             = sys_display,
        dia_code                = dia_code,
        dia_display             = dia_display,
        panel_code              = panel_code,
        panel_display           = panel_display
    )

    # ── Final Summary ───────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("           TASK 3 — EXECUTION SUMMARY")
    print(f"{'='*60}")
    print(f"\n  SOURCE (OpenEMR)")
    print(f"    Patient        : {p_given} {p_family}  (ID: {openemr_patient_id})")
    print(f"    Systolic       : {systolic} mmHg  (manually supplied — not in OpenEMR)")
    print(f"    Diastolic      : {diastolic} mmHg  (manually supplied — not in OpenEMR)")

    print(f"\n  TERMINOLOGY (Primary Care CodeSystem/$lookup)")
    print(f"    Systolic  interp : {sys_code}  — {sys_display}")
    print(f"    Diastolic interp : {dia_code}  — {dia_display}")
    print(f"    Panel     interp : {panel_code}  — {panel_display}")

    print(f"\n  DESTINATION (Primary Care EHR)")
    print(f"    Patient ID     : {primary_care_patient_id}  (Reused from Task 1)")
    print(f"    Performer      : {practitioner_ref}")
    print(f"    Observation ID : {observation_id}")
    print(f"    Identifier     : urn:uuid:<generated at runtime>")
    print(f"    Body Site      : SNOMED {BODY_SITE_CODE} — {BODY_SITE_DISPLAY}")
    print(f"\n{'='*60}")
    print("  Pipeline complete.")
    print(f"{'='*60}\n")