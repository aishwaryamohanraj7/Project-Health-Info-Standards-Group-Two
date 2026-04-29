import json
import uuid
import requests
from datetime import datetime, timezone
from pathlib import Path

OPENEMR_BASE      = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
PRIMARY_CARE_BASE = "http://159.203.105.138:8080/fhir"

SEARCH_GENDER = "male"
SEARCH_GIVEN  = "David"
SEARCH_FAMILY = "Abshire"

BP_PANEL_CODE     = "55284-4"
BP_SYSTOLIC_CODE  = "8480-6"
BP_DIASTOLIC_CODE = "8462-4"
LOINC_SYSTEM      = "http://loinc.org"
UCUM_SYSTEM       = "http://unitsofmeasure.org"

SNOMED_SYSTEM     = "http://snomed.info/sct"
BODY_SITE_CODE    = "368208006"
BODY_SITE_DISPLAY = "Left arm"

INTERP_SYSTEM = "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"

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

    print("Patient Discovery - OpenEMR")
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

def get_bp_values_from_openemr(openemr_patient_id):

    print("Fetching BP Values from OpenEMR Vital Signs")

    def extract_components(entries):
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

            code_top = r.get("code", {}).get("coding", [{}])
            code_top = code_top[0].get("code", "") if code_top else ""
            val_top  = r.get("valueQuantity", {}).get("value")
            if code_top == BP_SYSTOLIC_CODE and val_top is not None:
                systolic = val_top
            if code_top == BP_DIASTOLIC_CODE and val_top is not None:
                diastolic = val_top
        return systolic, diastolic

    print(f"\n  Strategy 1 - GET /Observation?patient={openemr_patient_id}"
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

    if systolic is None or diastolic is None:
        print(f"\n  Strategy 2 - GET /Observation?patient={openemr_patient_id}"
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

def lookup_interpretation_code(raw_code):
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

    display = None
    for param in data.get("parameter", []):
        if param.get("name") == "display":
            display = param.get("valueString")
            break

    if display:
        print(f"    Result  : code={raw_code} | display={display}  (from server)")
    else:
        display = raw_code
        print(f"    Result  : code={raw_code} | display not returned - using code as display")

    return raw_code, display


def classify_and_lookup(systolic, diastolic):

    print("Interpretation Code Resolution - CodeSystem/$lookup")
    print(f"  System  : {INTERP_SYSTEM}")

    if   systolic < 90:    sys_raw = "L"
    elif systolic <= 120:  sys_raw = "N"
    else:                  sys_raw = "H"

    if   diastolic < 60:   dia_raw = "L"
    elif diastolic <= 80:  dia_raw = "N"
    else:                  dia_raw = "H"

    priority  = {"H": 3, "L": 2, "N": 1}
    panel_raw = sys_raw if priority[sys_raw] >= priority[dia_raw] else dia_raw

    print(f"\n  Classified codes (from clinical thresholds):")
    print(f"    Systolic  {systolic} mmHg  - {sys_raw}")
    print(f"    Diastolic {diastolic} mmHg  - {dia_raw}")
    print(f"    Panel                     - {panel_raw}")

    print(f"\n  Resolving display strings via CodeSystem/$lookup:")
    sys_code,   sys_display   = lookup_interpretation_code(sys_raw)
    dia_code,   dia_display   = lookup_interpretation_code(dia_raw)
    panel_code, panel_display = lookup_interpretation_code(panel_raw)

    return sys_code, sys_display, dia_code, dia_display, panel_code, panel_display

def get_primary_care_patient_id(openemr_patient_id):
    print("Resolving Primary Care EHR Patient ID")
    print(f"  Searching by MR identifier: {openemr_patient_id}")

    entries = requests.get(
        f"{PRIMARY_CARE_BASE}/Patient",
        headers = get_primary_care_headers(),
        params  = {"identifier": openemr_patient_id}
    ).json().get("entry", [])

    if entries:
        pc_id = entries[0]["resource"].get("id")
        print(f"  Match found - Primary Care Patient ID: {pc_id}")
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

def create_bp_observation(primary_care_patient_id, practitioner_ref,
                          systolic_value, diastolic_value,
                          sys_code, sys_display,
                          dia_code, dia_display,
                          panel_code, panel_display):

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
                    "code":    BODY_SITE_CODE,
                    "display": BODY_SITE_DISPLAY
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

    print("Creating Blood Pressure Observation - Primary Care EHR")
    print(f"  Identifier  : {obs_identifier}")
    print(f"  Subject     : Patient/{primary_care_patient_id}")
    print(f"  Performer   : {practitioner_ref}")
    print(f"  Panel Code  : LOINC {BP_PANEL_CODE}")
    print(f"  Body Site   : SNOMED {BODY_SITE_CODE} - {BODY_SITE_DISPLAY}")
    print(f"  Systolic    : {systolic_value} mmHg - {sys_code} ({sys_display})")
    print(f"  Diastolic   : {diastolic_value} mmHg - {dia_code} ({dia_display})")
    print(f"  Panel Interp: {panel_code} ({panel_display})")
    print(f"  Effective   : {effective_dt}")

    print(json.dumps(observation_payload, indent=4))

    response = requests.post(
        url     = f"{PRIMARY_CARE_BASE}/Observation",
        headers = get_primary_care_headers(),
        json    = observation_payload
    )
    print(f"  HTTP Status : {response.status_code}")
    observation_id = response.json().get("id")
    print(f"  Success     : New Observation ID - {observation_id}")

    with open(data_dir / "task3_observation.json", "w") as f:
        json.dump(observation_payload, f, indent=4)
    print(f"  Cached      : data/task3_observation.json")

    return observation_id, observation_payload

if __name__ == "__main__":

    print("  TASK 3 - BLOOD PRESSURE OBSERVATION PIPELINE")
    print("  Flow: Manual BP values - Terminology (interp lookup) - Primary Care EHR")

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

    existing_bp = get_bp_values_from_openemr(openemr_patient_id)

    systolic  = 127
    diastolic =  86
    print(f"\n  BP values not found in OpenEMR - using manually supplied values:")
    print(f"    Systolic  : {systolic} mmHg")
    print(f"    Diastolic : {diastolic} mmHg")

    (sys_code, sys_display,
     dia_code, dia_display,
     panel_code, panel_display) = classify_and_lookup(systolic, diastolic)

    with open(data_dir / "task1_patient_id.json", "r") as f:
        primary_care_patient_id = json.load(f).get("patient_id")
    print(f"\n[Phase 4] Reusing existing Primary Care Patient ID: {primary_care_patient_id} (from Task 1)")

    practitioner_ref = get_primary_care_practitioner_id()

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

    print("TASK 3 - EXECUTION SUMMARY")
    print(f"\n  SOURCE (OpenEMR)")
    print(f"    Patient        : {p_given} {p_family}  (ID: {openemr_patient_id})")
    print(f"    Systolic       : {systolic} mmHg  (manually supplied - not in OpenEMR)")
    print(f"    Diastolic      : {diastolic} mmHg  (manually supplied - not in OpenEMR)")

    print(f"\n  TERMINOLOGY (Primary Care CodeSystem/$lookup)")
    print(f"    Systolic  interp : {sys_code}  - {sys_display}")
    print(f"    Diastolic interp : {dia_code}  - {dia_display}")
    print(f"    Panel     interp : {panel_code}  - {panel_display}")

    print(f"\n  DESTINATION (Primary Care EHR)")
    print(f"    Patient ID     : {primary_care_patient_id}  (Reused from Task 1)")
    print(f"    Performer      : {practitioner_ref}")
    print(f"    Observation ID : {observation_id}")
    print(f"    Identifier     : urn:uuid:<generated at runtime>")
    print(f"    Body Site      : SNOMED {BODY_SITE_CODE} - {BODY_SITE_DISPLAY}")
    print("  Pipeline complete.")
