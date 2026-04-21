import json
import requests
from pathlib import Path
from datetime import datetime
from hl7apy.core import Message

# -------------------------------
# BASE URLs
# -------------------------------
OPENEMR_BASE = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"
HERMES_BASE  = "http://159.203.121.13:8080/v1/snomed"

# -------------------------------
# YOUR PATIENT + CONDITION
# -------------------------------
PATIENT_ID = "4804"
SNOMED_CODE = "13645005"   # COPD

# Fallback
FALLBACK_SNOMED = "Chronic obstructive pulmonary disease"
FALLBACK_ICD = "J44.9"

# -------------------------------
# TOKEN
# -------------------------------
def get_access_token():
    file_path = Path(__file__).parent / "src" / "data" / "access_token.json"
    with open(file_path, "r") as f:
        return json.load(f)["access_token"]


HEADERS = {
    "Authorization": f"Bearer {get_access_token()}",
    "Accept": "application/json"
}


# -------------------------------
# STEP 1: GET PATIENT
# -------------------------------
def get_patient():

    url = f"{OPENEMR_BASE}/Patient/{PATIENT_ID}"
    res = requests.get(url, headers=HEADERS)

    patient = res.json()

    name = patient.get("name", [{}])[0]

    return {
        "id": patient.get("id"),
        "given": name.get("given", ["Unknown"])[0],
        "family": name.get("family", "Unknown"),
        "gender": "M" if patient.get("gender") == "male" else "F",
        "birth": patient.get("birthDate", "1900-01-01").replace("-", "")
    }


# -------------------------------
# STEP 2: SNOMED DISPLAY
# -------------------------------
def get_snomed_display(code):

    url = f"{HERMES_BASE}/concepts/{code}/extended"
    res = requests.get(url)

    if res.status_code != 200:
        return FALLBACK_SNOMED

    return res.json().get("preferredDescription", {}).get("term", FALLBACK_SNOMED)


# -------------------------------
# STEP 3: SNOMED → ICD
# -------------------------------
def get_icd(code):

    url = f"{HERMES_BASE}/concepts/{code}/refsets"
    res = requests.get(url)

    if res.status_code != 200:
        return FALLBACK_ICD

    data = res.json()

    if isinstance(data, dict):
        data = data.get("items", [])

    for item in data:
        if item.get("mapTarget"):
            return item["mapTarget"]

    return FALLBACK_ICD


# -------------------------------
# STEP 4: BUILD HL7
# -------------------------------
def build_hl7(patient, snomed_display, icd):

    msg = Message("ADT_A01", version="2.5")

    now = datetime.now().strftime("%Y%m%d%H%M%S")

    # MSH
    msg.msh.msh_3 = "OpenEMR"
    msg.msh.msh_4 = "Hospital"
    msg.msh.msh_5 = "PrimaryCare"
    msg.msh.msh_6 = "System"
    msg.msh.msh_7 = now
    msg.msh.msh_9 = "ADT^A01"
    msg.msh.msh_10 = "MSG001"
    msg.msh.msh_11 = "P"

    # PID
    msg.pid.pid_3 = patient["id"]
    msg.pid.pid_5 = f"{patient['family']}^{patient['given']}"
    msg.pid.pid_7 = patient["birth"]
    msg.pid.pid_8 = patient["gender"]

    # PV1
    msg.pv1.pv1_2 = "O"

    # DG1
    msg.dg1.dg1_1 = "1"
    msg.dg1.dg1_3 = f"{icd}^{snomed_display}"
    msg.dg1.dg1_6 = "A"

    return msg.to_er7()


# -------------------------------
# STEP 5: SAVE FILE
# -------------------------------
def save_file(msg):

    with open("hl7_message.txt", "w") as f:
        f.write(msg.replace("\r", "\r\n"))

    print("\n✅ HL7 FILE SAVED")


# -------------------------------
# MAIN
# -------------------------------
if __name__ == "__main__":

    patient = get_patient()

    print("\nPatient:", patient["given"], patient["family"])

    snomed_display = get_snomed_display(SNOMED_CODE)
    icd = get_icd(SNOMED_CODE)

    print("SNOMED:", snomed_display)
    print("ICD:", icd)

    hl7 = build_hl7(patient, snomed_display, icd)

    print("\n--- HL7 MESSAGE ---\n")
    print(hl7)

    save_file(hl7)