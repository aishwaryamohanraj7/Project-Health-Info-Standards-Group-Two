import requests

BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"

def search_patient_filtered(name, gender, birthdate):

    url = f"{BASE_URL}/Patient?name={name}&gender={gender}&birthdate=gt{birthdate}"
    response = requests.get(url)

    print(url)

    data = response.json()
    entries = data.get("entry", [])

    print(f"\nPatients Found: {len(entries)}")

    for e in entries:
        p = e["resource"]
        print(f"{p['id']} - {p['name'][0]['given'][0]} {p['name'][0]['family']}")

    return entries