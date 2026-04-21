import json
import requests
from pathlib import Path

# 🔹 OPENEMR BASE
OPENEMR_BASE = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"

# 🔹 YOUR PATIENT
PATIENT_ID = "4804"


# 🔹 TOKEN
def get_access_token():
    file_path = Path(__file__).parent / "src" / "data" / "access_token.json"
    with open(file_path, "r") as f:
        return json.load(f)["access_token"]


def get_headers():
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Accept": "application/json"
    }


# ✅ 🔥 FETCH BP FROM OPENEMR
def fetch_bp(patient_id):

    print("\n--- FETCHING BP FROM OPENEMR ---")

    url = f"{OPENEMR_BASE}/Observation"

    response = requests.get(
        url,
        headers=get_headers(),
        params={
            "patient": patient_id,
            "category": "vital-signs",
            "code": "85354-9"   # Blood Pressure panel
        }
    )

    print("URL:", response.url)
    print("Status Code:", response.status_code)

    data = response.json()
    entries = data.get("entry", [])

    if not entries:
        print("⚠️ No BP Observation found in OpenEMR")
        return

    print(f"\nTotal BP Records Found: {len(entries)}\n")

    # 🔹 Extract BP values
    resource = entries[0]["resource"]
    components = resource.get("component", [])

    systolic = None
    diastolic = None

    for comp in components:
        coding = comp.get("code", {}).get("coding", [])

        for c in coding:
            code = c.get("code")

            if code == "8480-6":   # systolic
                systolic = comp.get("valueQuantity", {}).get("value")

            elif code == "8462-4":  # diastolic
                diastolic = comp.get("valueQuantity", {}).get("value")

    print("Systolic:", systolic)
    print("Diastolic:", diastolic)


# 🔹 MAIN
if __name__ == "__main__":
    fetch_bp(PATIENT_ID)