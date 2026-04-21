import secrets
import string
import requests
import json
from pathlib import Path

EMAIL = "sample@gmail.com"
URL = "https://in-info-web20.luddy.indianapolis.iu.edu/oauth2/default/registration"

REDIRECT_URI = "https://client.example.org/callback"  # Also known as Callback URL
AUTH_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/oauth2/default/authorize"
TOKEN_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/oauth2/default/token"
SCOPE = "openid offline_access api:oemr api:fhir api:port user/allergy.read user/allergy.write user/appointment.read user/appointment.write user/dental_issue.read user/dental_issue.write user/document.read user/document.write user/drug.read user/encounter.read user/encounter.write user/facility.read user/facility.write user/immunization.read user/insurance.read user/insurance.write user/insurance_company.read user/insurance_company.write user/insurance_type.read user/list.read user/medical_problem.read user/medical_problem.write user/medication.read user/medication.write user/message.write user/patient.read user/patient.write user/practitioner.read user/practitioner.write user/prescription.read user/procedure.read user/soap_note.read user/soap_note.write user/surgery.read user/surgery.write user/transaction.read user/transaction.write user/vital.read user/vital.write user/AllergyIntolerance.read user/CareTeam.read user/Condition.read user/Coverage.read user/Encounter.read user/Immunization.read user/Location.read user/Medication.read user/MedicationRequest.read user/Observation.read user/Organization.read user/Organization.write user/Patient.read user/Patient.write user/Practitioner.read user/Practitioner.write user/PractitionerRole.read user/Procedure.read patient/Encounter.read patient/Patient.read patient/AllergyIntolerance.read patient/CareTeam.read patient/Condition.read patient/Coverage.read patient/Encounter.read patient/Immunization.read patient/MedicationRequest.read patient/Observation.read patient/Patient.read patient/Procedure.read"

data_dir = Path.cwd() / 'data'

STUDENT_NAME = "aishwarya_mohanraj"


def generate_random_string(length=12):
    characters = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    return ''.join(secrets.choice(characters) for _ in range(length))


def get_client_name(student_name):
    random_string = generate_random_string()
    client_name_string = f"{student_name}_{random_string}"
    print(client_name_string)
    return client_name_string


def get_client_registration_details():
    payload = json.dumps({
        "application_type": "private",
        "redirect_uris": [
            REDIRECT_URI
        ],
        "client_name": get_client_name(student_name=STUDENT_NAME),
        "contacts": [
            EMAIL
        ],
        "scope": SCOPE
    })
    headers = {
        'Content-Type': 'application/json',
        'content-type': 'application/json'
    }

    response = requests.request(method="POST", url=URL, headers=headers, data=payload)
    print(response)
    data = response.json()

    client_id = data['client_id']
    client_id_file_path = Path(data_dir / "client_id.txt")
    client_id_file_path.touch(exist_ok=True)
    with open(client_id_file_path, 'w') as f:
        f.write(client_id)

    client_secret = data['client_secret']
    client_secret_file_path = Path(data_dir / "client_secret.txt")
    client_secret_file_path.touch(exist_ok=True)
    with open(client_secret_file_path, 'w') as f:
        f.write(client_secret)

    return data


def get_client_id_from_file():
    file_path = Path(data_dir / "client_id.txt")
    with open(file_path, 'r') as f:
        client_id = f.readline()
        if len(client_id) == 0:
            raise ValueError("ValueError - No client_id found in client_id.txt")
        else:
            return client_id


def get_client_secret_from_file():
    file_path = Path(data_dir / "client_secret.txt")
    with open(file_path, 'r') as f:
        client_secret = f.readline()
        if len(client_secret) == 0:
            raise ValueError("ValueError - No client_secret found in client_secret.txt")
        else:
            return client_secret


if __name__ == '__main__':
    pass
