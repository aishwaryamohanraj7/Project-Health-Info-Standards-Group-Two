import requests
import json

BASE_URL = "http://159.203.105.138:8080/fhir"

headers = {
    "Content-Type": "application/fhir+json"
}

def create_patient():
    patient_data = {
        "resourceType": "Patient",
        "meta": {
            "profile": [
                "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"
            ]
        },
        "identifier": [
            {
                "system": "http://hospital.smarthealthit.org",
                "value": "MRN-ABSHIRE-001"
            }
        ],
        "active": True,
        "name": [
            {
                "use": "official",
                "family": "Abshire",
                "given": ["David"]
            }
        ],
        "gender": "male",
        "birthDate": "1996-09-29",
        "deceasedBoolean": False,
        "address": [
            {
                "line": ["393 Cole Knoll Unit 63"],
                "city": "Malden",
                "district": "Boston",
                "state": "Massachusetts",
                "postalCode": "02155",
                "country": "USA"
            }
        ],
        "telecom": [
            {
                "system": "phone",
                "value": "555-123-4567",
                "use": "home"
            },
            {
                "system": "email",
                "value": "david.abshire@example.com",
                "use": "home"
            }
        ]
    }

    response = requests.post(
        f"{BASE_URL}/Patient",
        headers=headers,
        json=patient_data
    )

    print("\n--- Patient Created ---")
    print("Status:", response.status_code)
    print("Response:", response.json())

    # Save patient ID for next step
    patient_id = response.json()["id"]
    print("\nPatient ID:", patient_id)

    return patient_id


if __name__ == "__main__":
    create_patient()