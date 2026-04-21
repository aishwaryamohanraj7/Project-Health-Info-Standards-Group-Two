import json
import requests
from pathlib import Path
from src.registration import data_dir

BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"


# -------- AUTH --------
def get_access_token():
    file_path = Path(data_dir / "access_token.json")
    with open(file_path, 'r') as f:
        return json.load(f).get("access_token")


def get_headers():
    return {
        "Authorization": f"Bearer {get_access_token()}"
    }


# -------- 1. SEARCH PATIENT USING PARAMETERS --------
def search_specific_patient():
    url = f"{BASE_URL}/Patient?given=David&family=Abshire&gender=male"
    response = requests.get(url, headers=get_headers())

    print("\n--- Specific Patient Query ---")
    print(response.url)

    data = response.json()

    print("\n--- Patient Found ---")

    for entry in data.get("entry", []):
        patient = entry["resource"]

        pid = patient["id"]
        given = patient["name"][0]["given"][0]
        family = patient["name"][0]["family"]
        gender = patient.get("gender")
        birthdate = patient.get("birthDate")

        print(f"ID: {pid}")
        print(f"Name: {given} {family}")
        print(f"Gender: {gender}")
        print(f"Birth Date: {birthdate}")


# -------- 2. FILTERED SEARCH QUERY --------
def filtered_search():
    url = f"{BASE_URL}/Patient?name=Abshire&birthdate=gt1996-09-29"
    response = requests.get(url, headers=get_headers())

    print("\n--- Filtered Search Query ---")
    print(response.url)

    data = response.json()

    print(f"\nNumber of matching patients: {len(data.get('entry', []))}")


# -------- MAIN --------
if __name__ == "__main__":
    search_specific_patient()
    filtered_search()