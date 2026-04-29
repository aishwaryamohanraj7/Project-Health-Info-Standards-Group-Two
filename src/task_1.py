import json
import requests
from pathlib import Path

# Endpoint Configurations
OPENEMR_BASE = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
HERMES_BASE = "http://159.203.121.13:8080/v1/snomed"
PRIMARY_CARE_BASE = "http://159.203.105.138:8080/fhir"

#FHIR Profiles
PATIENT_PROFILE = "http://example.org/StructureDefinition/my-patient-profile"
CONDITION_PROFILE = "http://example.org/StructureDefinition/my-condition-profile"

#Patient Criteria
SEARCH_GENDER = "male"
SEARCH_GIVEN = "David"
SEARCH_FAMILY = "Abshire"

data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)

def get_access_token():
    """Extracts the authorization token from the local JSON file."""
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
        "Accept": "application/fhir+json"
    }

def search_patient():
    url = f"{OPENEMR_BASE}/Patient"
    params = {
        "given": SEARCH_GIVEN,
        "family": SEARCH_FAMILY,
        "gender": SEARCH_GENDER
    }

    print(f"\nExecuting Patient Discovery")
    print(f"Request URI: GET /Patient?given={SEARCH_GIVEN}&family={SEARCH_FAMILY}&gender={SEARCH_GENDER}")
    print(f"Awaiting: FHIR Bundle containing candidate profiles.")

    response = requests.get(url=url, headers=get_openemr_headers(), params=params)
    data = response.json()
    entries = data.get("entry", [])
    print(f"Total individuals identified: {len(entries)}. Displaying top 10.")

    for i, entry in enumerate(entries[:10]):
        resource = entry["resource"]
        patient_id = resource.get("id")
        name = resource.get("name", [{}])[0]
        given = name.get("given", [""])[0]
        family = name.get("family", "")
        gender_val = resource.get("gender", "unknown")
        dob = resource.get("birthDate", "unknown")
        deceased = resource.get("deceasedBoolean") or resource.get("deceasedDateTime")
        print(f"[{i}] Record ID: {patient_id} | Individual: {given} {family} | Sex: {gender_val} | Born: {dob} | Deceased Status: {deceased}")

    return entries

def get_patient_conditions(patient_id):
    url = f"{OPENEMR_BASE}/Condition"
    params = {"patient": patient_id}

    print(f"\nFetching Clinical Records for ID: {patient_id}")

    response = requests.get(url=url, headers=get_openemr_headers(), params=params)
    data = response.json()
    entries = data.get("entry", [])

    print(f"Total clinical issues retrieved: {len(entries)}. Displaying complete list.")

    if not entries:
        print("Warning: No clinical problems documented for this individual.")
        return None

    for i, entry in enumerate(entries):
        resource = entry["resource"]
        code_field = resource.get("code", {})
        codings = code_field.get("coding", [])
        if codings:
            display = codings[0].get("display", "unknown")
            system = codings[0].get("system", "unknown")
        else:
            display = code_field.get("text", "unknown")
            system = "text-only"
        print(f"[{i}] Terminology: {display} | Code System: {system}")

    return entries

def search_snomed_by_text(search_term):
    print(f"Querying Hermes API for string: '{search_term}'")
    response = requests.get(
        f"{HERMES_BASE}/search",
        params={"s": search_term, "constraint": "<404684003", "maxHits": 1}
    )
    data = response.json()
    items = data if isinstance(data, list) else data.get("items", [])

    if not items:
        return None, None

    concept_id = items[0].get("conceptId") or items[0].get("id")
    preferred_term = items[0].get("preferredTerm") or items[0].get("term", search_term)
    print(f"Match Acquired: {concept_id} | {preferred_term}")

    print("\nRaw Hermes JSON Payload")
    print(json.dumps(data, indent=4))

    return concept_id, preferred_term

def get_parent_concept(snomed_code):
    print(f"\nAscending SNOMED Hierarchy for Concept: {snomed_code}")

    response = requests.get(f"{HERMES_BASE}/concepts/{snomed_code}/extended")
    data = response.json()

    direct_parents = data.get("directParentRelationships", {}).get("116680003", [])
    if not direct_parents:
        print("Alert: Reached top level; no IS-A parent mapped.")
        return None, None

    parent_id = direct_parents[0]
    print(f"Superior Concept ID identified: {parent_id}")

    parent_response = requests.get(f"{HERMES_BASE}/concepts/{parent_id}/extended")
    parent_data = parent_response.json()
    preferred_term = parent_data.get("preferredDescription", {}).get("term", "unknown")
    print(f"Superior Description: {preferred_term}")

    return parent_id, preferred_term

def create_patient_on_primary_care(openemr_patient_resource):
    name = openemr_patient_resource.get("name", [{}])[0]
    given = name.get("given", ["Unknown"])
    family = name.get("family", "Unknown")
    gender = openemr_patient_resource.get("gender", "unknown")
    birth_date = openemr_patient_resource.get("birthDate", "1900-01-01")
    identifier_value = openemr_patient_resource.get("id", "unknown")
    address = openemr_patient_resource.get("address", [{}])[0]
    address_line = address.get("line", ["Unknown"])
    city = address.get("city", "Unknown")
    district = address.get("district", "Unknown")
    state = address.get("state", "Unknown")
    postal_code = address.get("postalCode", "Unknown")
    address_text = f"{', '.join(address_line)}, {city}, {district}, {state} {postal_code}"
    patient_payload = {
        "resourceType": "Patient",
        "meta": {"profile": [PATIENT_PROFILE]},
        "text": {
            "status": "generated",
            "div": f'<div xmlns="http://www.w3.org/1999/xhtml">Individual: {given[0]} {family}, Sex: {gender}, Born: {birth_date}</div>'
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
                "value": identifier_value
            }
        ],
        "active": True,
        "name": [{"use": "official", "family": family, "given": given}],
        "gender": gender,
        "birthDate": birth_date,
        "deceasedBoolean": False,
        "address": [
            {
                "use": "home",
                "type": "both",
                "line": address_line,
                "city": city,
                "district": district,
                "state": state,
                "postalCode": postal_code,
                "text": address_text
            }
        ]
    }
    print(f"\nInitiating Patient Transfer to Target EHR")
    print(f"Target: {given[0]} {family} | Active Status: True | Gender: {gender} | DOB: {birth_date}")
    print(f"Address: {address_text}")
    response = requests.post(
        url=f"{PRIMARY_CARE_BASE}/Patient",
        headers=get_primary_care_headers(),
        json=patient_payload
    )
    created = response.json()
    patient_id = created.get("id")
    print(f"Transfer successful. New Local ID assigned: {patient_id}")

    with open(data_dir / "patient.json", "w") as f:
        json.dump(patient_payload, f, indent=4)
    print(f"Resource cached locally at: data/patient.json")

    with open(data_dir / "task1_patient_id.json", "w") as f:
        json.dump({"patient_id": patient_id}, f, indent=4)

    return patient_id, patient_payload

def create_condition_on_primary_care(primary_care_patient_id, parent_concept_id, parent_term):
    condition_payload = {
        "resourceType": "Condition",
        "meta": {"profile": [CONDITION_PROFILE]},
        "text": {
            "status": "generated",
            "div": f'<div xmlns="http://www.w3.org/1999/xhtml">Clinical Issue: {parent_term} (Code: {parent_concept_id})</div>'
        },
        "clinicalStatus": {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
        },
        "verificationStatus": {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                        "code": "problem-list-item",
                        "display": "Problem List Item"
                    }
                ]
            }
        ],
        "severity": {
            "coding": [{"system": "http://snomed.info/sct", "code": "6736007", "display": "Moderate"}]
        },
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": str(parent_concept_id),
                    "display": parent_term
                }
            ],
            "text": parent_term
        },
        "bodySite": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "38266002",
                        "display": "Entire body as a whole"
                    }
                ]
            }
        ],
        "subject": {"reference": f"Patient/{primary_care_patient_id}"},
        "onsetDateTime": "2024-01-01T00:00:00+00:00"
    }

    print(f"\nPushing New Condition to Target EHR")
    print(f"Injecting Parent Terminology: {parent_concept_id} | {parent_term}")
    print(f"Subject Reference ID: {primary_care_patient_id}")

    response = requests.post(
        url=f"{PRIMARY_CARE_BASE}/Condition",
        headers=get_primary_care_headers(),
        json=condition_payload
    )
    created = response.json()
    condition_id = created.get("id")
    print(f"Creation acknowledged. New Condition ID assigned: {condition_id}")

    with open(data_dir / "condition.json", "w") as f:
        json.dump(condition_payload, f, indent=4)
    print(f"Resource cached locally at: data/condition.json")

    return condition_id, condition_payload

def validate_resource(resource_type, resource_payload):
    url = f"{PRIMARY_CARE_BASE}/{resource_type}/$validate"
    print(f"\nExecuting Profile Validation for: {resource_type}")
    print(f"Target URI: POST {url}")
    print(f"Applied Standard: {resource_payload.get('meta', {}).get('profile', ['Unknown Standard'])[0]}")

    response = requests.post(url=url, headers=get_primary_care_headers(), json=resource_payload)
    print(f"HTTP Status Received: {response.status_code}")

    data = response.json()
    issues = data.get("issue", [])
    for issue in issues:
        severity = issue.get("severity")
        if severity in ("error", "warning"):
            print(f"  [{severity.upper()}] Diagnostics: {issue.get('diagnostics', 'No diagnostic details provided')}")

    return response.status_code, data

if __name__ == "__main__":
    print(" WORKFLOW PIPELINE INITIATED ")
    print("Data Flow: Source (OpenEMR) -> Terminology (Hermes) -> Destination (Primary Care EHR)")

    patients = search_patient()
    selected_patient = None
    patient_id = None
    snomed_code = None
    condition_display = None

    for patient_entry in patients:
        candidate = patient_entry["resource"]

        if candidate.get("deceasedBoolean") or candidate.get("deceasedDateTime"):
            continue

        candidate_id = candidate["id"]
        candidate_name = candidate.get("name", [{}])[0]
        print(f"\nEvaluating Profile: {candidate_name.get('given', [''])[0]} {candidate_name.get('family', '')} (Internal ID: {candidate_id})")

        conds = get_patient_conditions(candidate_id)
        if not conds:
            continue

        found_snomed_code = None
        found_display = None
        found_condition = None

        target_condition = "Chronic Obstructive Pulmonary Disease"

        for entry in conds:
            resource = entry["resource"]
            code_field = resource.get("code", {})
            codings = code_field.get("coding", [])
            text = code_field.get("text", "")

            display = ""
            if codings:
                display = codings[0].get("display", "")

            if "obstructive pulmonary" in text.lower() or "obstructive pulmonary" in display.lower():
                looked_up_id, looked_up_term = search_snomed_by_text(target_condition)
                if looked_up_id:
                    found_snomed_code = str(looked_up_id)
                    found_display = looked_up_term
                    found_condition = resource
                    break

        if found_snomed_code and found_condition:
            selected_patient = candidate
            patient_id = candidate_id
            snomed_code = found_snomed_code
            condition_display = found_display
            print(f"Isolated Clinical Focus: {condition_display} (Code: {snomed_code})")
            break

    if not selected_patient or not snomed_code:
        print("\n[FATAL] Unable to locate candidate possessing the specified clinical criteria.")
        print("Troubleshooting: Authorization may have expired. Try refreshing token.")
        exit(1)

    parent_id, parent_term = get_parent_concept(snomed_code)
    primary_care_patient_id, patient_payload = create_patient_on_primary_care(selected_patient)

    if parent_id and parent_term:
        primary_care_condition_id, condition_payload = create_condition_on_primary_care(
            primary_care_patient_id, parent_id, parent_term
        )
    else:
        print("\n[FATAL] Hierarchy mapping failed. Halting process before Load/Validate.")
        exit(1)
    patient_status_code, patient_data = validate_resource("Patient", patient_payload)
    patient_errors = len([i for i in patient_data.get("issue", []) if i.get("severity") == "error"])

    condition_status_code, condition_data = validate_resource("Condition", condition_payload)
    condition_errors = len([i for i in condition_data.get("issue", []) if i.get("severity") == "error"])

    print("\n>> EXECUTION SUMMARY")
    patient_name = selected_patient.get("name", [{}])[0]
    print(f"\n>> SOURCE DATA EXTRACTION:")
    print(f"   API Params: GET /Patient?given={SEARCH_GIVEN}&family={SEARCH_FAMILY}&gender={SEARCH_GENDER}")
    print(f"   Demographics: {patient_name.get('given', [''])[0]} {patient_name.get('family', '')} (Record ID: {patient_id})")
    print(f"   Target Condition: {condition_display}")
    print(f"   Registered SNOMED: {snomed_code}")

    print(f"\n>> TERMINOLOGY TRANSFORMATION:")
    print(f"   Input Concept: {snomed_code} ({condition_display})")
    print(f"   Resolved Parent: {parent_id} ({parent_term})")
    print(f"   Hierarchy Path: Ascended via standard IS-A (116680003) linkage")

    print(f"\n>> DESTINATION LOADING:")
    print(f"   Patient Record: Generated ID {primary_care_patient_id}")
    print(f"   Status Tags: Active=True | Deceased=False")
    print(f"   Condition Record: Generated ID {primary_care_condition_id}")
    print(f"   Applied Concept Mapping: {parent_id} ({parent_term})")

    print(f"\n>> PROFILE COMPLIANCE VALIDATION:")
    print(f"   Patient Guidelines: {PATIENT_PROFILE}")
    print(f"   Condition Guidelines: {CONDITION_PROFILE}")
    print(f"   Verification Protocol: REST POST to /$validate endpoint")
    print(f"   Patient Status: {'VERIFIED' if patient_errors == 0 else f'REJECTED ({patient_errors} errors identified)'}")
    print(f"   Condition Status: {'VERIFIED' if condition_errors == 0 else f'REJECTED ({condition_errors} errors identified)'}")