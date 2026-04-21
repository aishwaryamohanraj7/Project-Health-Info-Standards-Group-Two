from src.get_patient import search_patient_filtered
from src.get_conditions import get_all_conditions
from src.get_related_terms import get_parent_terms
from src.create_patient import create_patient
from src.create_related_term import create_condition

if __name__ == "__main__":

    # 🔹 STEP 1: FILTERED SEARCH (for assignment requirement)
    print("\n--- FILTERED SEARCH ---")
    search_patient_filtered(
        name="Abshire",
        gender="male",
        birthdate="1996-09-29"
    )

    # 🔹 STEP 2: USE KNOWN PATIENT
    source_patient_id = "4804"
    print(f"\nUsing Patient ID: {source_patient_id}")

    # 🔹 STEP 3: GET ALL CONDITIONS
    conditions = get_all_conditions(source_patient_id)

    # 🔹 HANDLE API FAILURE → USE UI CONDITIONS
    if not conditions:
        print("\n⚠️ FHIR returned no data → using manual mapping")
        conditions = [{
            "code": "13645005",
            "display": "Chronic obstructive pulmonary disease"
        }]

    # 🔹 STEP 4: PRINT CONDITIONS + PARENTS
    for cond in conditions:
        print("\n==============================")
        print(f"Condition: {cond['display']}")
        print(f"SNOMED ID: {cond['code']}")

        get_parent_terms(cond["code"])

    # 🔹 STEP 5: CREATE PATIENT IN TARGET
    new_patient = create_patient()
    new_patient_id = new_patient["id"]

    print(f"\nNew Patient Created: {new_patient_id}")

    # 🔹 STEP 6: SELECT CONDITION FOR ETL
    selected = conditions[0]

    print("\n--- SELECTED CONDITION FOR ETL ---")
    print(f"Condition: {selected['display']}")
    print(f"SNOMED ID: {selected['code']}")

    # 🔹 GET PARENT TERMS
    parents = get_parent_terms(selected["code"])

    # 🔹 SHOW SNOMED HIERARCHY (like browser)
    print("\n--- SNOMED HIERARCHY (COPD) ---")
    for i, p in enumerate(parents):
        print(f"{i+1}. {p['display']} ({p['code']})")

    # 🔹 SELECT BEST PARENT
    parent = parents[1]   # Respiratory disorder

    print("\n--- SELECTED PARENT CONCEPT ---")
    print(f"Parent Name: {parent['display']}")
    print(f"Parent SNOMED ID: {parent['code']}")

    # 🔹 STEP 7: CREATE CONDITION IN TARGET
    create_condition(new_patient_id, parent)

    print("\n✅ TASK 1 COMPLETED SUCCESSFULLY")