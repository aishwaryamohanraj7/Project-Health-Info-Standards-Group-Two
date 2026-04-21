def get_parent_terms(concept_id):

    print("\n--- PARENT TERMS ---")

    if concept_id == "13645005":  # COPD

        parents = [
            {"code": "19829001", "display": "Chronic disease of respiratory system"},
            {"code": "50043002", "display": "Respiratory disorder"},
            {"code": "312437006", "display": "Tracheobronchial disorder"}
        ]

        for p in parents:
            print(f"{p['display']} (SNOMED: {p['code']})")

        return parents

    print("⚠️ No mapping → using fallback")

    return [{
        "code": "301227004",
        "display": "Respiratory finding"
    }]