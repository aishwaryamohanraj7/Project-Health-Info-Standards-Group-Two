import requests
import json

BASE_URL = "http://159.203.105.138:8080/fhir"

headers = {
    "Content-Type": "application/fhir+json"
}

# ✅ Your Patient Resource ID
PATIENT_ID = "443"


def create_condition():
    condition_data = {
        "resourceType": "Condition",
        "meta": {
            "profile": [
                "http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition"
            ]
        },

        # ✅ Clinical Status
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                    "display": "Active"
                }
            ]
        },

        # ✅ Verification Status
        "verificationStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed",
                    "display": "Confirmed"
                }
            ]
        },

        # ✅ CORRECT CATEGORY (Encounter Diagnosis)
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

        # ✅ Parent SNOMED Concept
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "17097001",
                    "display": "Chronic disease of respiratory system"
                }
            ],
            "text": "Chronic disease of respiratory system"
        },

        # ✅ Severity
        "severity": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "24484000",
                    "display": "Severe"
                }
            ]
        },

        # ✅ Body Site
        "bodySite": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "39607008",
                        "display": "Lung structure"
                    }
                ]
            }
        ],

        # ✅ Onset
        "onsetDateTime": "2023-01-01T00:00:00Z",

        # ✅ Link to Patient
        "subject": {
            "reference": f"Patient/{PATIENT_ID}"
        }
    }

    response = requests.post(
        f"{BASE_URL}/Condition",
        headers=headers,
        json=condition_data
    )

    print("\n--- Condition Created ---")
    print("Status Code:", response.status_code)
    print("Response:", response.json())


if __name__ == "__main__":
    create_condition()