import requests

BASE_URL = "http://159.203.105.138:8080/fhir"

def create_condition(patient_id, term):

    url = f"{BASE_URL}/Condition"

    condition = {
        "resourceType": "Condition",

        "subject": {
            "reference": f"Patient/{patient_id}"
        },

        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": term["code"],
                    "display": term["display"]
                }
            ],
            "text": term["display"]
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

    response = requests.post(url, json=condition)

    print("\n--- CREATE CONDITION ---")
    print("Status:", response.status_code)
    print(response.text)