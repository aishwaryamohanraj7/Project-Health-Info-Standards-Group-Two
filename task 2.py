import requests
import json

BASE_URL = "http://159.203.105.138:8080/fhir"

def create_child_condition(patient_id):

    url = f"{BASE_URL}/Condition"

    condition_resource = {
        "resourceType": "Condition",

        # REQUIRED FOR VALIDATION
        "meta": {
            "profile": [
                "http://hl7.org/fhir/StructureDefinition/Condition"
            ]
        },

        # NARRATIVE (UPDATED)
        "text": {
            "status": "generated",
            "div": "<div>Acute exacerbation of chronic obstructive pulmonary disease</div>"
        },

        "subject": {
            "reference": f"Patient/{patient_id}"
        },

        # CHILD CONCEPT (COPD)
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

        # CATEGORY
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

        # ✅ STATUS
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                    "display": "Active"
                }
            ]
        },

        "verificationStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed",
                    "display": "Confirmed"
                }
            ]
        },

        # SEVERITY (appropriate for exacerbation)
        "severity": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "24484000",
                    "display": "Severe"
                }
            ]
        },

        # BODY SITE (COPD-specific)
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

        # ONSET
        "onsetDateTime": "2024-01-01T00:00:00Z"
    }

    response = requests.post(
        url,
        headers={"Content-Type": "application/fhir+json"},
        json=condition_resource
    )

    print("\n--- COPD CHILD CONDITION CREATED ---")
    print("Status Code:", response.status_code)

    data = response.json()

    print("Condition ID:", data.get("id"))
    print("Patient Ref :", data.get("subject", {}).get("reference"))
    print("Condition   :", data.get("code", {}).get("coding", [{}])[0].get("display"))

    return data.get("id")


if __name__ == "__main__":
    create_child_condition("383")