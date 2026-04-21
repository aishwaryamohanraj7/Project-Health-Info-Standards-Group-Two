import requests
import json

BASE_URL = "http://159.203.105.138:8080/fhir"


# 🔹 VALIDATE PATIENT
def validate_patient():

    url = f"{BASE_URL}/Patient/$validate"

    patient = {
        "resourceType": "Patient",

        "meta": {
            "profile": [
                "http://hl7.org/fhir/StructureDefinition/Patient"
            ]
        },

        "text": {
            "status": "generated",
            "div": "<div xmlns='http://www.w3.org/1999/xhtml'>Patient: David Abshire</div>"
        },

        "name": [
            {
                "given": ["David"],
                "family": "Abshire"
            }
        ],
        "gender": "male",
        "birthDate": "1996-09-29"
    }

    res = requests.post(
        url,
        headers={"Content-Type": "application/fhir+json"},
        json=patient
    )

    print("\n--- PATIENT VALIDATION ---")
    print("Status:", res.status_code)
    print(json.dumps(res.json(), indent=4))


# 🔹 VALIDATE CONDITION
def validate_condition(patient_id):

    url = f"{BASE_URL}/Condition/$validate"

    condition = {
        "resourceType": "Condition",

        "meta": {
            "profile": [
                "http://hl7.org/fhir/StructureDefinition/Condition"
            ]
        },

        "text": {
            "status": "generated",
            "div": "<div xmlns='http://www.w3.org/1999/xhtml'>Condition: Respiratory disorder</div>"
        },

        "subject": {
            "reference": f"Patient/{patient_id}"
        },

        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "50043002",
                    "display": "Respiratory disorder"
                }
            ]
        },

        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active"
                }
            ]
        },

        "verificationStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed"
                }
            ]
        }
    }

    res = requests.post(
        url,
        headers={"Content-Type": "application/fhir+json"},
        json=condition
    )

    print("\n--- CONDITION VALIDATION ---")
    print("Status:", res.status_code)
    print(json.dumps(res.json(), indent=4))


# 🔹 MAIN
if __name__ == "__main__":

    # 👉 use your latest created patient ID
    validate_patient()
    validate_condition("278")