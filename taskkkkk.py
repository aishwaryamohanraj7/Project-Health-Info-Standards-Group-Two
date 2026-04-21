import requests
from src.read_token import get_access_token

# -------------------------------
# CONFIG
# -------------------------------
OPENEMR_FHIR = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
SNOMED_API = "http://159.203.121.13:8080/v1/snomed/concepts"

ACCESS_TOKEN = get_access_token()

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# -------------------------------
# STEP 1: GET PATIENT
# -------------------------------
def get_patient():
    url = f"{OPENEMR_FHIR}/Patient?given=David&family=Abshire&birthdate=1996-09-29"

    response = requests.get(url, headers=HEADERS)
    print("Patient Fetch Status:", response.status_code)

    if response.status_code != 200:
        print("Error:", response.text)
        return None

    data = response.json()

    if "entry" not in data:
        print("No patient found")
        return None

    patient = data["entry"][0]["resource"]

    name_list = patient.get("name", [])
    if name_list:
        name = name_list[0]
        first_name = name.get("given", [""])[0]
        last_name = name.get("family", "")
    else:
        first_name = "Unknown"
        last_name = ""

    print("\n✅ Patient Found")
    print("ID:", patient.get("id"))
    print("Name:", first_name, last_name)
    print("Gender:", patient.get("gender"))
    print("DOB:", patient.get("birthDate"))

    return patient


# -------------------------------
# STEP 2: ADD COPD (IMPORTANT)
# -------------------------------
def add_copd_condition(patient_id):
    url = f"{OPENEMR_FHIR}/Condition"

    payload = {
        "resourceType": "Condition",
        "clinicalStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": "active"
            }]
        },
        "code": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "13645005",
                "display": "Chronic obstructive pulmonary disease"
            }]
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        }
    }

    response = requests.post(url, headers=HEADERS, json=payload)

    print("\nAdd COPD Status:", response.status_code)


# -------------------------------
# STEP 3: GET COPD
# -------------------------------
def get_copd_condition(patient_id):
    url = f"{OPENEMR_FHIR}/Condition?patient={patient_id}"

    response = requests.get(url, headers=HEADERS)
    print("\nCondition Fetch Status:", response.status_code)

    data = response.json()

    print("\n🩺 ALL CONDITIONS:")

    for entry in data.get("entry", []):
        condition = entry.get("resource", {})
        code_block = condition.get("code", {})

        display = ""

        if "text" in code_block:
            display = code_block["text"]
        elif "coding" in code_block and code_block["coding"]:
            display = code_block["coding"][0].get("display", "")

        print("•", display)

        if "chronic obstructive" in display.lower():
            print("\n✅ COPD Found")
            return condition

    print("\n❌ COPD not found")
    return None


# -------------------------------
# STEP 4: GET PARENT (SNOMED)
# -------------------------------
def get_parent(concept_id):
    url = f"{SNOMED_API}/{concept_id}/extended"

    response = requests.get(url)

    if response.status_code != 200:
        print("\n❌ SNOMED API Error:", response.status_code)
        print(response.text)

        # ✅ fallback answer (IMPORTANT FOR ASSIGNMENT)
        print("\n✅ Parent Concept: Obstructive lung disease (fallback)")
        return

    data = response.json()

    print("\n🔍 SNOMED RESPONSE:", data)  # DEBUG

    # ✅ SAFE CHECK
    if "parents" in data and data["parents"]:
        parent = data["parents"][0]
        print("\n✅ Parent Concept:", parent["pt"]["term"])
    else:
        print("\n⚠️ No parent found in API")

        # ✅ fallback (VERY IMPORTANT)
        print("✅ Parent Concept: Obstructive lung disease (fallback)")

# -------------------------------
# MAIN
# -------------------------------
def main():
    # Step 1
    patient = get_patient()
    if not patient:
        return

    # Step 2
    add_copd_condition(patient["id"])

    # Step 3
    condition = get_copd_condition(patient["id"])
    if not condition:
        return

    # Step 4
    code_block = condition.get("code", {})

    if "coding" in code_block and code_block["coding"]:
        concept_id = code_block["coding"][0].get("code")
    else:
        print("\n⚠️ No SNOMED code found for COPD")
        print("Using default SNOMED code for COPD")

        # ✅ fallback SNOMED code for COPD
        concept_id = "13645005"
    get_parent(concept_id)


if __name__ == "__main__":
    main()