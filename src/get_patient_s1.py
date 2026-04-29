import json
import requests
from pathlib import Path
from src.registration import data_dir

BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"


# -------- AUTH --------
def get_access_token():
    try:
        file_path = Path(data_dir / "access_token.json")
        with open(file_path, 'r') as f:
            return json.load(f).get("access_token")
    except Exception as e:
        print("❌ Error reading access token:", e)
        return None


def get_headers():
    token = get_access_token()
    if not token:
        raise Exception("❌ No access token found. Check your access_token.json file.")
    return {
        "Authorization": f"Bearer {token}"
    }


# -------- 1. SEARCH PATIENT USING PARAMETERS --------
def search_specific_patient():
    url = f"{BASE_URL}/Patient?given=David&family=Abshire&gender=male"
    response = requests.get(url, headers=get_headers())

    print("\n--- Specific Patient Query ---")
    print("URL:", response.url)
    print("Status Code:", response.status_code)

    if response.status_code != 200:
        print("❌ Request failed")
        print(response.text)
        return

    data = response.json()

    if "entry" not in data:
        print("⚠️ No patients found.")
        print(data)
        return

    print("\n--- Patient Found ---")

    for entry in data.get("entry", []):
        patient = entry["resource"]

        pid = patient.get("id", "N/A")
        given = patient.get("name", [{}])[0].get("given", ["N/A"])[0]
        family = patient.get("name", [{}])[0].get("family", "N/A")
        gender = patient.get("gender", "N/A")
        birthdate = patient.get("birthDate", "N/A")

        print(f"\nID: {pid}")
        print(f"Name: {given} {family}")
        print(f"Gender: {gender}")
        print(f"Birth Date: {birthdate}")


# -------- 2. FILTERED SEARCH QUERY --------
def filtered_search():
    url = f"{BASE_URL}/Patient?name=Abshire&birthdate=gt1996-09-29"
    response = requests.get(url, headers=get_headers())

    print("\n--- Filtered Search Query ---")
    print("URL:", response.url)
    print("Status Code:", response.status_code)

    if response.status_code != 200:
        print("❌ Request failed")
        print(response.text)
        return

    data = response.json()

    if "entry" not in data:
        print("⚠️ No matching patients found.")
        print(data)
        return

    print(f"\nNumber of matching patients: {len(data.get('entry', []))}")


# -------- MAIN --------
if __name__ == "__main__":
    print("🚀 Running Patient Search Script...\n")
    search_specific_patient()
    filtered_search()