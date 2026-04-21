import requests
import json

BASE_URL = "http://159.203.105.138:8080/fhir"

headers = {
    "Content-Type": "application/fhir+json"
}

# 🔴 SAME patient ID you used earlier
PATIENT_ID = "383"


def validate_condition():
    url = f"{BASE_URL}/Condition/$validate"

    condition_resource = {
        "resourceType": "Condition",

        # ✅ REQUIRED: meta profile
        "meta": {
            "profile": [
                "http://hl7.org/fhir/StructureDefinition/Condition"
            ]
        },

        # ✅ Narrative (removes warning)
        "text": {
            "status": "generated",
            "div": "<div xmlns='http://www.w3.org/1999/xhtml'>Acute exacerbation of chronic obstructive pulmonary disease</div>"
        },

        "subject": {
            "reference": f"Patient/{PATIENT_ID}"
        },

        # ✅ CHILD COPD CONCEPT
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "195951007",
                    "display": "Acute exacerbation of chronic obstructive pulmonary disease"
                }
            ],
            "text": "Acute exacerbation of chronic obstructive pulmonary disease"
        },

        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                        "code": "encounter-diagnosis",
                        "display": "Encounter Diagnosis"
                    }
                ]
            }
        ],

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
        },

        "severity": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "24484000",
                    "display": "Severe"
                }
            ]
        },

        "bodySite": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "955009",
                        "display": "Bronchial structure"
                    }
                ]
            }
        ],

        "onsetDateTime": "2024-01-01T00:00:00Z"
    }

    response = requests.post(url, headers=headers, json=condition_resource)

    print("\n--- CONDITION VALIDATION ---")
    print("Status Code:", response.status_code)
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    validate_condition()