import requests

HERMES_BASE = "http://159.203.121.13:8080/v1/snomed"

# COPD SNOMED
COPD_CODE = "13645005"


def get_parent_concept(code):

    print("\n--- GET PARENT CONCEPT (HERMES ECL) ---")

    url = f"{HERMES_BASE}/search"

    params = {
        "constraint": f">!{code}",   # 👈 direct parents
        "maxHits": 5
    }

    response = requests.get(url, params=params)

    print("URL:", response.url)
    print("Status:", response.status_code)

    if response.status_code != 200:
        print("❌ ERROR:", response.text)
        return []

    data = response.json()

    # Handle both formats
    if isinstance(data, dict):
        items = data.get("items", [])
    else:
        items = data

    parents = []

    for item in items:
        concept_id = item.get("conceptId") or item.get("id")
        term = item.get("preferredTerm") or item.get("term")

        parents.append({
            "code": concept_id,
            "display": term
        })

    return parents


# MAIN
if __name__ == "__main__":

    parents = get_parent_concept(COPD_CODE)

    if not parents:
        print("⚠️ No parent concepts found")
    else:
        print("\n--- PARENT TERMS ---")
        for p in parents:
            print(f"{p['display']} (SNOMED: {p['code']})")