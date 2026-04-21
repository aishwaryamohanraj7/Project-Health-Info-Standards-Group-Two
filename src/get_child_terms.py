# src/get_child_terms.py

def get_child_terms(concept_id):

    print("\n--- CHILD TERMS ---")

    if concept_id == "13645005":  # COPD CONDITION

        children = [
            {"code": "195951007", "display": "Acute exacerbation of COPD"},
            {"code": "185086009", "display": "Chronic obstructive bronchitis"}
        ]

        for c in children:
            print(f"{c['display']} (SNOMED: {c['code']})")

        return children

    print("⚠️ No child mapping → using fallback")

    return [{
        "code": "195951007",
        "display": "Acute exacerbation of COPD"


    }]