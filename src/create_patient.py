import requests

BASE_URL = "http://159.203.105.138:8080/fhir"

def create_patient():

    url = f"{BASE_URL}/Patient"

    patient = {
        "resourceType": "Patient",
        "active": True,

        "identifier": [
            {
                "system": "http://hospital.smarthealth.org/mrn",
                "value": "MRN-ABSHIRE-001"
            }
        ],

        "name": [
            {
                "given": ["David"],
                "family": "Abshire"
            }
        ],

        "gender": "male",
        "birthDate": "1996-09-29",
        "deceasedBoolean": False,

        "address": [
            {
                "line": ["393 Cole Knoll Unit 63"],
                "city": "Malden",
                "district": "NA",
                "state": "Massachusetts",
                "postalCode": "02155",
                "country": "USA"
            }
        ]
    }

    response = requests.post(url, json=patient)

    print("\n--- CREATE PATIENT ---")
    print("Status:", response.status_code)

    return response.json()