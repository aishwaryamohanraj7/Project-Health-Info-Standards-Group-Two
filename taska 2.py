import requests

HERMES_BASE = "http://159.203.121.13:8080/v1/snomed"

# COPD SNOMED
COPD_CODE = "13645005"


def get_child_concept(code):

    print("\n--- GET CHILD CONCEPT (HERMES ECL) ---")

    url = f"{HERMES_BASE}/search"

    params = {
        "constraint": f"<!{code}",   # 👈 direct children
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

    children = []

    for item in items:
        concept_id = item.get("conceptId") or item.get("id")
        term = item.get("preferredTerm") or item.get("term")

        children.append({
            "code": concept_id,
            "display": term
        })

    return children


# MAIN
if __name__ == "__main__":

    children = get_child_concept(COPD_CODE)

    if not children:
        print("⚠️ No child concepts found")
    else:
        print("\n--- CHILD TERMS ---")
        for c in children:
            print(f"{c['display']} (SNOMED: {c['code']})")