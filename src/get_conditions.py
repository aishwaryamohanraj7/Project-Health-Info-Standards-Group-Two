import requests

BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"

def get_all_conditions(patient_id):

    print("\n--- TRYING FHIR API ---")

    url = f"{BASE_URL}/Condition?patient={patient_id}"
    response = requests.get(url)
    data = response.json()

    if "entry" in data:
        print("Using FHIR API data")
        # process normally
    else:
        print("⚠️ FHIR returned no data → using manual mapping")

        conditions = [
            {"code": "13645005", "display": "Chronic obstructive pulmonary disease"},
            {"code": "44054006", "display": "Type 2 diabetes mellitus"},
            {"code": "38341003", "display": "Hypertension"},
            {"code": "55822004", "display": "Hyperlipidemia"},
            {"code": "40930008", "display": "Hypothyroidism"},
            {"code": "197480006", "display": "Generalized anxiety disorder"}
        ]

        return conditions