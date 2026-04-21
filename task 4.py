import requests
import json

BASE_URL = "http://159.203.105.138:8080/fhir"


def create_procedure(patient_id):

    url = f"{BASE_URL}/Procedure"

    procedure = {
        "resourceType": "Procedure",

        "status": "completed",

        "category": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "103693007",
                    "display": "Diagnostic procedure"
                }
            ]
        },

        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "168731009",
                    "display": "Chest X-ray"
                }
            ],
            "text": "Chest X-ray"
        },

        "subject": {
            "reference": f"Patient/{patient_id}"
        },

        "performedDateTime": "2026-04-19T11:00:00Z",

        "performer": [
            {
                "actor": {
                    "reference": "Practitioner/8"
                }
            }
        ],

        "reasonCode": [
            {
                "text": "Evaluation of respiratory condition"
            }
        ]
    }

    response = requests.post(
        url,
        headers={"Content-Type": "application/fhir+json"},
        json=procedure
    )

    print("\n--- CREATE PROCEDURE ---")
    print("Status:", response.status_code)

    try:
        print(json.dumps(response.json(), indent=4))
    except:
        print(response.text)


# ✅ MAIN
if __name__ == "__main__":
    create_procedure("278")   # 👈 replace with your patient ID