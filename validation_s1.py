import requests
import json

BASE_URL = "http://159.203.105.138:8080/fhir"

headers = {
    "Content-Type": "application/fhir+json"
}


# -------- VALIDATE PATIENT --------
def validate_patient():
    patient_resource = {
        "resourceType": "Patient",

        # ✅ Base profile (no error)
        "meta": {
            "profile": [
                "http://hl7.org/fhir/StructureDefinition/Patient"
            ]
        },

        # ✅ removes warning
        "text": {
            "status": "generated",
            "div": "<div xmlns='http://www.w3.org/1999/xhtml'>Patient: David Abshire</div>"
        },

        "active": True,
        "name": [
            {
                "family": "Abshire",
                "given": ["David"]
            }
        ],
        "gender": "male",
        "birthDate": "1996-09-29"
    }

    res = requests.post(f"{BASE_URL}/Patient/$validate", headers=headers, json=patient_resource)

    print("\n--- PATIENT VALIDATION ---")
    print(res.status_code)
    print(json.dumps(res.json(), indent=2))


# -------- VALIDATE CONDITION --------
def validate_condition():
    condition_resource = {
        "resourceType": "Condition",

        # ✅ Base profile (no error)
        "meta": {
            "profile": [
                "http://hl7.org/fhir/StructureDefinition/Condition"
            ]
        },

        # ✅ removes warning
        "text": {
            "status": "generated",
            "div": "<div xmlns='http://www.w3.org/1999/xhtml'>Condition: Chronic disease of respiratory system</div>"
        },

        "subject": {
            "reference": "Patient/443"
        },

        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "17097001",
                    "display": "Chronic disease of respiratory system"
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

    res = requests.post(f"{BASE_URL}/Condition/$validate", headers=headers, json=condition_resource)

    print("\n--- CONDITION VALIDATION ---")
    print(res.status_code)
    print(json.dumps(res.json(), indent=2))


# -------- RUN --------
if __name__ == "__main__":
    validate_patient()
    validate_condition()