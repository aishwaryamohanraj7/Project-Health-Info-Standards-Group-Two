import requests
import json
from pathlib import Path

# ==============================
# CONFIG
# ==============================
OPENEMR_FHIR = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
TARGET_FHIR = "http://159.203.105.138:8080/fhir"

SOURCE_PATIENT_ID = "4804"   # OpenEMR patient
TARGET_PATIENT_ID = "398"    # Your created patient


# ==============================
# TOKEN
# ==============================
def get_access_token():
    file_path = Path(__file__).resolve().parent / "src" / "data" / "access_token.json"
    with open(file_path, "r") as f:
        return json.load(f)["access_token"]


HEADERS = {
    "Authorization": f"Bearer {get_access_token()}",
    "Accept": "application/fhir+json"
}


# ==============================
# STEP 1: FETCH PROCEDURES FROM OPENEMR
# ==============================
def fetch_procedures():

    print("\n--- FETCHING PROCEDURES FROM OPENEMR ---")

    url = f"{OPENEMR_FHIR}/Procedure?patient={SOURCE_PATIENT_ID}"
    res = requests.get(url, headers=HEADERS)

    print("URL:", url)
    print("Status:", res.status_code)

    data = res.json()

    if "entry" not in data:
        print("No procedures found in OpenEMR")
        return

    print("\nProcedures in OpenEMR:")

    for entry in data["entry"]:
        resource = entry["resource"]

        proc_id = resource.get("id", "")

        code = resource.get("code", {})
        text = code.get("text")

        if not text:
            coding = code.get("coding", [])
            if coding:
                text = coding[0].get("display", "")

        print(f"Procedure ID: {proc_id} → {text}")


# ==============================
# STEP 2: CREATE PROCEDURE (PRIMARY CARE)
# ==============================
def create_procedure():

    print("\n--- CREATING PROCEDURE IN PRIMARY CARE ---")

    url = f"{TARGET_FHIR}/Procedure"

    procedure = {
        "resourceType": "Procedure",

        "status": "completed",

        # Required for UI
        "category": {
            "text": "Imaging"
        },

        #  SNOMED code
        "code": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "168537006",
                "display": "Chest X-ray"
            }],
            "text": "Chest X-ray"
        },

        "subject": {
            "reference": f"Patient/{TARGET_PATIENT_ID}"
        },

        #  Date
        "performedDateTime": "2024-01-01T10:00:00Z",

        #  Performer
        "performer": [{
            "actor": {
                "reference": "Practitioner/8",
                "display": "Dr. John Smith"
            }
        }],

        # Follow up
        "followUp": [{
            "text": "Review in next visit"
        }],

        #  Notes
        "note": [{
            "text": "Chest X-ray completed successfully"
        }]
    }

    res = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {get_access_token()}",
            "Content-Type": "application/fhir+json"
        },
        json=procedure
    )

    print("Status:", res.status_code)
    print(res.text)


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":

    print("\n=== TASK 4 STARTED ===")

    # Step 1: Check OpenEMR
    fetch_procedures()

    # Step 2: Create Procedure in Primary Care
    create_procedure()

    print("\nTASK 4 COMPLETED")