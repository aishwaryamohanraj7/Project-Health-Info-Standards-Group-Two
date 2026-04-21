import requests
import json
import uuid

BASE_URL = "http://159.203.105.138:8080/fhir"


def create_blood_pressure(patient_id):

    url = f"{BASE_URL}/Observation"

    observation = {
        "resourceType": "Observation",

        # ✅ Identifier (for UI)
        "identifier": [
            {
                "system": "urn:ietf:rfc:3986",
                "value": f"urn:uuid:{uuid.uuid4()}"
            }
        ],

        "status": "final",

        # ✅ Category
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs"
                    }
                ]
            }
        ],

        # ✅ Blood Pressure Code (LOINC)
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "85354-9",
                    "display": "Blood pressure panel"
                }
            ],
            "text": "Blood Pressure"
        },

        # ✅ Patient Link
        "subject": {
            "reference": f"Patient/{patient_id}"
        },

        # ✅ Performer (for UI)
        "performer": [
            {
                "reference": "Practitioner/8"
            }
        ],

        "effectiveDateTime": "2026-04-19T10:00:00Z",

        # ✅ 🔥 BODY SITE (FIXED)
        "bodySite": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "368209003",
                        "display": "Right arm"
                    }
                ],
                "text": "Right arm"
            }
        ],

        # ✅ Components (Systolic + Diastolic)
        "component": [
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8480-6",
                            "display": "Systolic blood pressure"
                        }
                    ]
                },
                "valueQuantity": {
                    "value": 140,
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]"
                },

                # ✅ Interpretation (HIGH)
                "interpretation": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                                "code": "H",
                                "display": "high"
                            }
                        ]
                    }
                ]
            },
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8462-4",
                            "display": "Diastolic blood pressure"
                        }
                    ]
                },
                "valueQuantity": {
                    "value": 80,
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]"
                },

                # ✅ Interpretation (NORMAL)
                "interpretation": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                                "code": "N",
                                "display": "normal"
                            }
                        ]
                    }
                ]
            }
        ]
    }

    response = requests.post(
        url,
        headers={"Content-Type": "application/fhir+json"},
        json=observation
    )

    print("\n--- CREATE OBSERVATION ---")
    print("Status:", response.status_code)

    try:
        print(json.dumps(response.json(), indent=4))
    except:
        print(response.text)


# ✅ MAIN
if __name__ == "__main__":
    create_blood_pressure("278")   # 👈 replace with your patient ID