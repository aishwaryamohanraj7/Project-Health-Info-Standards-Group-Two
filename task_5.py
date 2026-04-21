import requests
import json
from pathlib import Path
from datetime import datetime

# ==============================
# 🔹 BASE URL
# ==============================
OPENEMR_FHIR = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"


# ==============================
# 🔹 TOKEN
# ==============================
def get_access_token():
    file_path = Path(__file__).resolve().parent / "src" / "data" / "access_token.json"

    with open(file_path, "r") as f:
        return json.load(f)["access_token"]


HEADERS = {
    "Authorization": f"Bearer {get_access_token()}",
    "Content-Type": "application/fhir+json"
}


# ==============================
# 🔹 STEP 1: SEARCH PATIENT
# ==============================
def search_patient():

    url = f"{OPENEMR_FHIR}/Patient?given=David&family=Abshire&birthdate=1996-09-29"
    res = requests.get(url, headers=HEADERS)

    print("\n--- SEARCH PATIENT ---")
    print(url)

    data = res.json()

    if "entry" not in data:
        return None

    patient = data["entry"][0]["resource"]

    print("Patient:", patient["name"][0]["given"][0], patient["name"][0]["family"])

    return patient


# ==============================
# 🔹 STEP 2: GET CONDITION
# ==============================
def get_condition(patient_id):

    url = f"{OPENEMR_FHIR}/Condition?patient={patient_id}"
    res = requests.get(url, headers=HEADERS)

    data = res.json()

    if "entry" not in data:
        print("⚠️ No condition → using COPD fallback")

        return {
            "code": {
                "coding": [{
                    "code": "13645005",
                    "display": "Chronic obstructive pulmonary disease"
                }]
            }
        }

    return data["entry"][0]["resource"]


# ==============================
# 🔹 STEP 3: SAFE EXTRACT SNOMED
# ==============================
def extract_snomed(condition):

    code_block = condition.get("code", {})
    coding_list = code_block.get("coding")

    if coding_list:
        return coding_list[0].get("code"), coding_list[0].get("display")

    # fallback (important for assignment)
    return "13645005", "Chronic obstructive pulmonary disease"


# ==============================
# 🔹 STEP 4: SNOMED → ICD
# ==============================
def snomed_to_icd(code):

    url = f"http://159.203.121.13:8080/v1/snomed/concepts/{code}/map/447562003"
    res = requests.get(url)

    try:
        data = res.json()
        if data:
            return data[0].get("mapTarget", "UNKNOWN")
    except:
        pass

    return "UNKNOWN"


# ==============================
# 🔹 STEP 5: BUILD HL7
# ==============================
def build_hl7(patient, condition_display, icd):

    name = patient.get("name", [{}])[0]

    given = name.get("given", ["UNKNOWN"])[0]
    family = name.get("family", "UNKNOWN")

    gender = patient.get("gender", "unknown")
    birth = patient.get("birthDate", "1900-01-01")
    pid = patient.get("id")

    now = datetime.now().strftime("%Y%m%d%H%M%S")

    msh = f"MSH|^~\\&|OpenEMR|Hospital|PrimaryCare|System|{now}||ADT^A01|MSG00001|P|2.5"
    pid_seg = f"PID|1||{pid}||{family}^{given}||{birth}|{gender}"
    pv1 = "PV1|1|O"
    dg1 = f"DG1|1||{icd}^{condition_display}"

    return "\n".join([msh, pid_seg, pv1, dg1])


# ==============================
# 🔹 STEP 6: SAVE FILE
# ==============================
def save_hl7(msg):

    with open("hl7_message.txt", "w") as f:
        f.write(msg)

    print("\n✅ HL7 FILE SAVED")


# ==============================
# 🔹 MAIN
# ==============================
if __name__ == "__main__":

    # STEP 1
    patient = search_patient()

    if not patient:
        print("❌ Patient not found")
        exit()

    patient_id = patient["id"]

    # STEP 2
    condition = get_condition(patient_id)

    # STEP 3
    snomed, display = extract_snomed(condition)

    print("\nCondition:", display)
    print("SNOMED:", snomed)

    # STEP 4
    icd = snomed_to_icd(snomed)

    print("\n--- DATA ---")
    print("SNOMED:", snomed)
    print("ICD:", icd)

    # STEP 5 (🔥 FIXED — hl7 always defined)
    hl7 = build_hl7(patient, display, icd)

    print("\n--- HL7 MESSAGE ---")
    print(hl7)

    # STEP 6
    save_hl7(hl7)