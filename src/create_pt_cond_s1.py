import requests

# SNOMED API BASE
SNOMED_API = "http://159.203.121.13:8080/v1/snomed/concepts"

# COPD SNOMED
COPD_CODE = "13645005"


def get_child_terms(concept_id):
    print("\n--- CHILD TERMS FROM SNOMED API ---")

    url = f"{SNOMED_API}/{concept_id}/children"

    params = {
        "catalog": "SYM_SNO_INT_USEXT",
        "contentModel": "4ef5b2c1-7e75-433a-84a7-57d02df2c0d7"
    }

    response = requests.get(url, params=params)

    print("URL:", response.url)

    if response.status_code != 200:
        print("❌ Error fetching child terms")
        print(response.text)
        return None

    data = response.json()

    if not data:
        print("⚠️ No child terms found")
        return None

    children = []

    for item in data:
        term = item.get("RelatedTerm", {})

        code = term.get("TermSourceCode")
        display = term.get("TermDescription")

        if code and display:
            print(f"{display} (SNOMED: {code})")

            children.append({
                "code": code,
                "display": display
            })

    return children


# -------- MAIN --------
if __name__ == "__main__":
    get_child_terms(COPD_CODE)