from src.get_conditions import get_all_conditions
from src.get_child_terms import get_child_terms
from src.create_related_term import create_condition

if __name__ == "__main__":

    # 🔹 USE SAME PATIENT FROM TASK 1
    patient_id = "278"   # 👈 replace with your latest ID

    print(f"\nUsing Patient ID: {patient_id}")

    # 🔹 GET CONDITIONS
    conditions = get_all_conditions("4804")

    if not conditions:
        print("\n⚠️ Using COPD fallback")
        conditions = [{
            "code": "13645005",
            "display": "Chronic obstructive pulmonary disease"
        }]

    # 🔹 SELECT COPD
    selected = conditions[0]

    print("\n--- SELECTED CONDITION ---")
    print(f"Condition: {selected['display']}")
    print(f"SNOMED ID: {selected['code']}")

    # 🔹 GET CHILD TERMS
    children = get_child_terms(selected["code"])

    # 🔹 SHOW CHILD OPTIONS
    print("\n--- SNOMED CHILD TERMS ---")
    for i, c in enumerate(children):
        print(f"{i+1}. {c['display']} ({c['code']})")

    # 🔹 SELECT CHILD
    child = children[0]

    print("\n--- SELECTED CHILD CONCEPT ---")
    print(f"Child Name: {child['display']}")
    print(f"Child SNOMED ID: {child['code']}")

    # 🔹 CREATE CONDITION (USING CHILD)
    create_condition(patient_id, child)

    print("\n✅ TASK 2 COMPLETED SUCCESSFULLY")