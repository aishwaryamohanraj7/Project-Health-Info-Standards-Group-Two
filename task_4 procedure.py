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


# ✅ 🔥 FETCH PROCEDURE FROM OPENEMR
def fetch_procedures(patient_id):
    print("\n--- FETCHING PROCEDURES FROM OPENEMR ---")

    url = f"{OPENEMR_BASE}/Procedure"

    response = requests.get(
        url,
        headers=get_headers(),
        params={"patient": patient_id}
    )

    print("URL:", response.url)
    print("Status Code:", response.status_code)

    data = response.json()

    entries = data.get("entry", [])

    if not entries:
        print("⚠️ No procedures found in OpenEMR")
        return

    print(f"\nTotal Procedures Found: {len(entries)}\n")

    # ✅ SAME STYLE AS YOUR FRIEND
    for i, entry in enumerate(entries):

        resource = entry.get("resource", {})
        proc_id = resource.get("id", "")

        code_block = resource.get("code", {})
        coding = code_block.get("coding", [])

        if coding:
            code = coding[0].get("code")
            display = coding[0].get("display")
            system = coding[0].get("system")
        else:
            code = "N/A"
            display = code_block.get("text", "Unknown")
            system = "text-only"

        print(f"[{i}] Procedure ID: {proc_id}")
        print(f"     Code: {code}")
        print(f"     Display: {display}")
        print(f"     System: {system}")
        print("-----------------------------------")


# 🔹 MAIN
if __name__ == "__main__":
    fetch_procedures(PATIENT_ID)