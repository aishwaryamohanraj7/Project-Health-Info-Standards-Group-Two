import requests
import json

BASE_URL = "http://159.203.105.138:8080/fhir"

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
            "div": "<div xmlns='http://www.w3.org/1999/xhtml'>Acute exacerbation of COPD</div>"
        },

        "subject": {
            "reference": f"Patient/{patient_id}"
        },

        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "195951007",
                    "display": "Acute exacerbation of COPD"
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

    print("\n--- TASK 2 CONDITION VALIDATION ---")
    print("Status:", res.status_code)
    print(json.dumps(res.json(), indent=4))


if __name__ == "__main__":
    validate_condition("278")   # 👈 your patient ID