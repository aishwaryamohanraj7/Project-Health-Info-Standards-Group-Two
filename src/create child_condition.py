def create_child_condition(patient_id, child_code, child_display):

    url = f"{TARGET_BASE}/Condition"

    condition_json = {
        "resourceType": "Condition",

        "clinicalStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": "active",
                "display": "Active"
            }]
        },

        "verificationStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                "code": "confirmed",
                "display": "Confirmed"
            }]
        },

        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                "code": "encounter-diagnosis",
                "display": "Encounter Diagnosis"
            }]
        }],

        "code": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": child_code,
                "display": child_display
            }],
            "text": child_display
        },

        "subject": {
            "reference": f"Patient/{patient_id}"
        },

        # 🔥 SAME REQUIRED FIELDS
        "severity": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "24484000",
                "display": "Severe"
            }]
        },

        "bodySite": [{
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "955009",
                "display": "Bronchial structure"
            }]
        }],

        "onsetDateTime": "2024-01-01T00:00:00Z"
    }

    res = requests.post(url, headers={"Content-Type": "application/fhir+json"}, json=condition_json)

    print("\n--- CHILD CONDITION CREATED ---")
    print("Status:", res.status_code)