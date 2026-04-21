import requests
import json
import uuid
from pathlib import Path

# ==============================
# CONFIG
# ==============================
OPENEMR_FHIR = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
TARGET_FHIR = "http://159.203.105.138:8080/fhir"

SOURCE_PATIENT_ID = "4804"
TARGET_PATIENT_ID = "278"


# ==============================
# TOKEN
# ==============================
def get_access_token():
    file_path = Path(__file__).resolve().parent / "src" / "data" / "access_token.json"
    with open(file_path, "r") as f:
        return json.load(f)["access_token"]


HEADERS = {
    "Authorization": f"Bearer {get_access_token()}",
    "Accept": "application/fhir+json"
}


# ==============================
# STEP 1: FETCH BP FROM OPENEMR
# ==============================
def fetch_bp():

    print("\n--- FETCHING BP FROM OPENEMR ---")

    url = f"{OPENEMR_FHIR}/Observation?patient={SOURCE_PATIENT_ID}"
    res = requests.get(url, headers=HEADERS)

    print("Status:", res.status_code)

    data = res.json()

    if "entry" not in data:
        print(" No observations found")
        return

    for entry in data.get("entry", []):
        obs = entry["resource"]

        coding = obs.get("code", {}).get("coding", [])
        if coding and coding[0].get("code") == "85354-9":
            print(" BP found in OpenEMR")
            return

    print("BP not found")


# ==============================
# STEP 2: CREATE BP
# ==============================
def create_bp():

    print("\n--- CREATING FINAL BP ---")

    url = f"{TARGET_FHIR}/Observation"

    observation = {
        "resourceType": "Observation",

        "status": "final",

        #  IDENTIFIER (FINAL FIX)
        "identifier": [{
            "system": "urn:ietf:rfc:3986",
            "value": f"urn:uuid:{uuid.uuid4()}"
        }],

        #  CATEGORY
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "vital-signs",
                "display": "Vital Signs"
            }]
        }],

        #  BP LOINC
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "85354-9",
                "display": "Blood pressure panel"
            }],
            "text": "Blood Pressure"
        },

        "subject": {
            "reference": f"Patient/{TARGET_PATIENT_ID}"
        },

        #  PERFORMER
        "performer": [{
            "reference": "Practitioner/8"
        }],

        "effectiveDateTime": "2026-04-19T10:00:00Z",

        #  BODY SITE (SNOMED)
        "bodySite": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "368209003",
                "display": "Right arm"
            }]
        },

        #  TOP INTERPRETATION
        "interpretation": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": "H",
                "display": "high"
            }]
        }],

        #  COMPONENTS
        "component": [

            #  SYSTOLIC
            {
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "8480-6",
                        "display": "Systolic blood pressure"
                    }]
                },
                "valueQuantity": {
                    "value": 140,
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org"
                },
                "interpretation": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": "H",
                        "display": "high"
                    }]
                }]
            },

            #  DIASTOLIC
            {
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "8462-4",
                        "display": "Diastolic blood pressure"
                    }]
                },
                "valueQuantity": {
                    "value": 80,
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org"
                },
                "interpretation": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": "N",
                        "display": "normal"
                    }]
                }]
            }
        ]
    }

    res = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {get_access_token()}",
            "Content-Type": "application/fhir+json"
        },
        json=observation
    )

    print("Status:", res.status_code)
    print(res.text)


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":

    print("\n=== TASK 3 START ===")

    fetch_bp()
    create_bp()

    print("\n TASK 3 COMPLETED")