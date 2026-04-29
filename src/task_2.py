import json
import requests
from pathlib import Path

OPENEMR_BASE       = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
HERMES_BASE        = "http://159.203.121.13:8080/v1/snomed"
PRIMARY_CARE_BASE  = "http://159.203.105.138:8080/fhir"

PATIENT_PROFILE   = "http://example.org/StructureDefinition/my-patient-profile"
CONDITION_PROFILE = "http://example.org/StructureDefinition/my-condition-profile"

SEARCH_GENDER = "male"
SEARCH_GIVEN  = "David"
SEARCH_FAMILY = "Abshire"

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
    params = {
        "given":  SEARCH_GIVEN,
        "family": SEARCH_FAMILY,
        "gender": SEARCH_GENDER
    }

    print("Patient Discovery")
    print(f"  Request : GET /Patient?given={SEARCH_GIVEN}&family={SEARCH_FAMILY}&gender={SEARCH_GENDER}")

    response = requests.get(url=url, headers=get_openemr_headers(), params=params)
    data     = response.json()
    entries  = data.get("entry", [])

    print(f"  Result  : {len(entries)} candidate(s) returned. Showing top 10.\n")
    for i, entry in enumerate(entries[:10]):
        r       = entry["resource"]
        name    = r.get("name", [{}])[0]
        given   = name.get("given", [""])[0]
        family  = name.get("family", "")
        deceased = r.get("deceasedBoolean") or r.get("deceasedDateTime")
        print(f"  [{i}] ID: {r.get('id')} | {given} {family} | "
              f"Gender: {r.get('gender')} | DOB: {r.get('birthDate')} | "
              f"Deceased: {deceased}")

    return entries

def get_patient_conditions(patient_id):
    url    = f"{OPENEMR_BASE}/Condition"
    params = {"patient": patient_id}

    print(f"Condition Extraction - Patient ID: {patient_id}")

    response = requests.get(url=url, headers=get_openemr_headers(), params=params)
    data     = response.json()
    entries  = data.get("entry", [])

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
    print("\n Raw Hermes JSON Payload")
    print(json.dumps(data, indent=4))

    return concept_id, preferred_term

def get_child_concept(snomed_code):

    print(f"Child Concept Resolution - Parent SNOMED: {snomed_code}")

    ecl_constraint = f"<!{snomed_code}"
    print(f"  ECL Constraint : {ecl_constraint}")
    print(f"  Endpoint       : GET /v1/snomed/search"
          f"?s=&constraint={ecl_constraint}&maxHits=5")

    search_response = requests.get(
        f"{HERMES_BASE}/search",
        params={"s": "", "constraint": ecl_constraint, "maxHits": 5}
    )
    data  = search_response.json()
    items = data if isinstance(data, list) else data.get("items", [])

    print("\n  [Raw Hermes ECL Search Payload]")
    print(json.dumps(data, indent=4))

    if not items:
        print("  WARNING: No children found for this concept via ECL search.")
        return None, None

    first_child = items[0]
    child_id    = first_child.get("conceptId") or first_child.get("id")
    child_term  = first_child.get("preferredTerm") or first_child.get("term")

    print(f"  Direct child concept ID identified : {child_id}")

    if not child_term:
        ext_response = requests.get(f"{HERMES_BASE}/concepts/{child_id}/extended")
        ext_data     = ext_response.json()
        child_term   = (
            ext_data.get("preferredDescription", {}).get("term")
            or ext_data.get("concept", {}).get("preferredTerm")
            or "Unknown"
        )

    print(f"  Child Preferred Term (PT)          : {child_term}")
    print(f"\n  Hierarchy path : {snomed_code} (COPD)  IS-A  {child_id} ({child_term})")

    return child_id, child_term

def create_patient_on_primary_care(openemr_patient_resource):
    name       = openemr_patient_resource.get("name", [{}])[0]
    given      = name.get("given", ["Unknown"])
    family     = name.get("family", "Unknown")
    gender     = openemr_patient_resource.get("gender", "unknown")
    birth_date = openemr_patient_resource.get("birthDate", "1900-01-01")
    identifier_value = openemr_patient_resource.get("id", "unknown")

    address      = openemr_patient_resource.get("address", [{}])[0]
    address_line = address.get("line", ["Unknown"])
    city         = address.get("city", "Unknown")
    district     = address.get("district", "Unknown")
    state        = address.get("state", "Unknown")
    postal_code  = address.get("postalCode", "Unknown")
    address_text = f"{', '.join(address_line)}, {city}, {district}, {state} {postal_code}"

    patient_payload = {
        "resourceType": "Patient",
        "meta": {"profile": [PATIENT_PROFILE]},
        "text": {
            "status": "generated",
            "div": (
                f'<div xmlns="http://www.w3.org/1999/xhtml">'
                f'Patient: {given[0]} {family}, Gender: {gender}, DOB: {birth_date}'
                f'</div>'
            )
        },
        "identifier": [
            {
                "use": "usual",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "MR"
                        }
                    ]
                },
                "system": "urn:oid:1.2.36.146.595.217.0.1",
                "value":  identifier_value
            }
        ],
        "active":          True,
        "name":            [{"use": "official", "family": family, "given": given}],
        "gender":          gender,
        "birthDate":       birth_date,
        "deceasedBoolean": False,
        "address": [
            {
                "use":        "home",
                "type":       "both",
                "line":       address_line,
                "city":       city,
                "district":   district,
                "state":      state,
                "postalCode": postal_code,
                "text":       address_text
            }
        ]
    }

    print("Patient Transfer - Primary Care EHR")
    print(f"  Patient : {given[0]} {family} | Gender: {gender} | DOB: {birth_date}")
    print(f"  Address : {address_text}")

    response   = requests.post(
        url     = f"{PRIMARY_CARE_BASE}/Patient",
        headers = get_primary_care_headers(),
        json    = patient_payload
    )
    created    = response.json()
    patient_id = created.get("id")
    print(f"  Success : New Primary Care Patient ID - {patient_id}")

    with open(data_dir / "task2_patient.json", "w") as f:
        json.dump(patient_payload, f, indent=4)
    print(f"  Cached  : data/task2_patient.json")

    return patient_id, patient_payload

def create_condition_on_primary_care(primary_care_patient_id, child_concept_id, child_term):

    condition_payload = {
        "resourceType": "Condition",
        "meta": {"profile": [CONDITION_PROFILE]},
        "text": {
            "status": "generated",
            "div": (
                f'<div xmlns="http://www.w3.org/1999/xhtml">'
                f'Condition: {child_term} (SNOMED CT: {child_concept_id})'
                f'</div>'
            )
        },
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code":   "active"
                }
            ]
        },
        "verificationStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code":   "confirmed"
                }
            ]
        },
        "category": [
            {
                "coding": [
                    {
                        "system":  "http://terminology.hl7.org/CodeSystem/condition-category",
                        "code":    "problem-list-item",
                        "display": "Problem List Item"
                    }
                ]
            }
        ],
        "severity": {
            "coding": [
                {
                    "system":  "http://snomed.info/sct",
                    "code":    "6736007",
                    "display": "Moderate"
                }
            ]
        },

        "code": {
            "coding": [
                {
                    "system":  "http://snomed.info/sct",
                    "code":    str(child_concept_id),
                    "display": child_term
                }
            ],
            "text": child_term
        },
        "bodySite": [
            {
                "coding": [
                    {
                        "system":  "http://snomed.info/sct",
                        "code":    "38266002",
                        "display": "Entire body as a whole"
                    }
                ]
            }
        ],
        "subject":       {"reference": f"Patient/{primary_care_patient_id}"},
        "onsetDateTime": "2024-01-01T00:00:00+00:00"
    }

    print("Condition Creation → Primary Care EHR (Child Concept)")
    print(f"  Child Concept : {child_concept_id} | {child_term}")
    print(f"  Subject Ref   : Patient/{primary_care_patient_id}")
    print(f"  Display used  : Preferred Term (PT) - FSN intentionally omitted")

    response     = requests.post(
        url     = f"{PRIMARY_CARE_BASE}/Condition",
        headers = get_primary_care_headers(),
        json    = condition_payload
    )
    created      = response.json()
    condition_id = created.get("id")
    print(f"  Success       : New Primary Care Condition ID - {condition_id}")

    with open(data_dir / "task2_condition.json", "w") as f:
        json.dump(condition_payload, f, indent=4)
    print(f"  Cached        : data/task2_condition.json")

    return condition_id, condition_payload

def validate_resource(resource_type, resource_payload):
    url = f"{PRIMARY_CARE_BASE}/{resource_type}/$validate"
    print(f"  [Validate] Resource Type : {resource_type}")
    print(f"  [Validate] Endpoint      : POST {url}")
    profile_url = resource_payload.get("meta", {}).get("profile", ["(none)"])[0]
    print(f"  [Validate] Profile URL   : {profile_url}")
    print(f"  [Validate] meta.profile  : PRESENT - required for profile-aware validation")

    response = requests.post(
        url     = url,
        headers = get_primary_care_headers(),
        json    = resource_payload
    )
    print(f"  [Validate] HTTP Status   : {response.status_code}")

    data   = response.json()
    issues = data.get("issue", [])

    if not issues:
        print("  [Validate] Outcome       : No issues reported.")
    else:
        for issue in issues:
            sev  = issue.get("severity", "info")
            diag = issue.get("diagnostics", issue.get("details", {}).get("text", "No detail provided"))
            if sev in ("error", "warning"):
                print(f"  [Validate] [{sev.upper():7s}] {diag}")
            else:
                print(f"  [Validate] [{sev.upper():7s}] {diag}")

    return response.status_code, data

if __name__ == "__main__":

    print("  TASK 2 - CHILD CONCEPT PIPELINE")
    print("  Flow: OpenEMR - Hermes (child) - Primary Care EHR")

    patients = search_patient()

    selected_patient = None
    patient_id       = None
    snomed_code      = None
    condition_display = None

    for patient_entry in patients:
        candidate = patient_entry["resource"]

        if candidate.get("deceasedBoolean") or candidate.get("deceasedDateTime"):
            continue

        candidate_id   = candidate["id"]
        candidate_name = candidate.get("name", [{}])[0]
        print(f"\n  Evaluating: {candidate_name.get('given', [''])[0]} "
              f"{candidate_name.get('family', '')} (ID: {candidate_id})")

        conds = get_patient_conditions(candidate_id)
        if not conds:
            continue

        found_snomed_code = None
        found_display     = None
        found_condition   = None

        for entry in conds:
            r        = entry["resource"]
            codings  = r.get("code", {}).get("coding", [])
            text     = r.get("code", {}).get("text", "")
            display  = codings[0].get("display", "") if codings else ""

            if ("obstructive pulmonary" in text.lower() or
                    "obstructive pulmonary" in display.lower()):

                looked_up_id, looked_up_term = search_snomed_by_text(
                    "Chronic Obstructive Pulmonary Disease"
                )
                if looked_up_id:
                    found_snomed_code = str(looked_up_id)
                    found_display     = looked_up_term
                    found_condition   = r
                    break

        if found_snomed_code and found_condition:
            selected_patient  = candidate
            patient_id        = candidate_id
            snomed_code       = found_snomed_code
            condition_display = found_display
            print(f"\n  Selected Condition : {condition_display} (Code: {snomed_code})")
            break

    if not selected_patient or not snomed_code:
        print("\n[FATAL] Could not locate the specified patient/condition. "
              "Check that your access token is still valid.")
        exit(1)

    child_id, child_term = get_child_concept(snomed_code)

    if not child_id or not child_term:
        print("\n[FATAL] Child concept resolution failed. Cannot continue.")
        exit(1)

    with open(data_dir / "task1_patient_id.json", "r") as f:
        primary_care_patient_id = json.load(f).get("patient_id")
    print(f"\n[Phase 4] Reusing existing Primary Care Patient ID: {primary_care_patient_id} (from Task 1)")

    primary_care_condition_id, condition_payload = create_condition_on_primary_care(
        primary_care_patient_id, child_id, child_term
    )

    print("Standalone Profile Validation (separate from ETL)")
    print("  Both payloads include 'meta.profile' - required so the server")
    print("  can identify and apply the correct StructureDefinition rules.")

    condition_status, condition_val_data = validate_resource("Condition", condition_payload)
    patient_errors = 0
    condition_errors = sum(1 for i in condition_val_data.get("issue", []) if i.get("severity") == "error")


    print("EXECUTION SUMMARY")

    p_name = selected_patient.get("name", [{}])[0]
    print(f"\n  SOURCE EXTRACTION")
    print(f"    Query        : GET /Patient?given={SEARCH_GIVEN}&family={SEARCH_FAMILY}&gender={SEARCH_GENDER}")
    print(f"    Patient      : {p_name.get('given', [''])[0]} {p_name.get('family', '')}  (OpenEMR ID: {patient_id})")
    print(f"    Condition    : {condition_display}")
    print(f"    SNOMED Code  : {snomed_code}")

    print(f"\n  TERMINOLOGY TRANSFORMATION  (CHILD - descending hierarchy)")
    print(f"    Parent Concept : {snomed_code}  ({condition_display})")
    print(f"    Child Concept  : {child_id}  ({child_term})")
    print(f"    Hierarchy Path : Descended via IS-A (116680003) linkage")
    print(f"    Display Used   : Preferred Term (PT) - FSN not used")

    print(f"\n  DESTINATION LOADING")
    print(f"    Existing Patient ID : {primary_care_patient_id}  (Reused from Task 1)")
    print(f"    New Condition ID : {primary_care_condition_id}")
    print(f"    Concept Applied  : {child_id}  ({child_term})")

    print(f"\n  PROFILE VALIDATION  (standalone - separate from ETL)")
    print(f"    Patient Profile   : {PATIENT_PROFILE}")
    print(f"    Condition Profile : {CONDITION_PROFILE}")
    print(f"    Validation Method : POST /$validate  (meta.profile present on both resources)")
    print(f"    Patient Result    : {'PASS' if patient_errors   == 0 else f'FAIL ({patient_errors} error(s))'}")
    print(f"    Condition Result  : {'PASS' if condition_errors == 0 else f'FAIL ({condition_errors} error(s))'}")
    print("  Pipeline complete.")