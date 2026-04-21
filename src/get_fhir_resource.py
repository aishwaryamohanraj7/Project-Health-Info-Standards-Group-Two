import json
import requests
from pprint import pprint
from pathlib import Path
from src.registration import data_dir

BASE_URL = "https://in-info-web20.luddy.indianapolis.iu.edu/apis/default/fhir"


def get_access_token_from_file():
    file_path = Path(data_dir / "access_token.json")
    if not file_path.exists():
        print("Error: access_token.json file not found.")
        return None
    try:
        with open(file_path, 'r') as json_file:
            json_data = json.load(json_file)
            access_token = json_data.get("access_token")
        return access_token
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error reading access token from file: {e}")
        return None


def get_headers():
    access_token = get_access_token_from_file()
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    return headers


def get_fhir_resource(resource_name):
    url = f'{BASE_URL}/{resource_name}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    pprint(response.json())


def get_fhir_patient(resource_id):
    url = f'{BASE_URL}/Patient/{resource_id}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    pprint(response.json())


def search_patient_by_name(name_string):
    url = f'{BASE_URL}/Patient?name={name_string}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    pprint(response.json())


def search_patient_by_name_gender(name_string, gender):
    url = f'{BASE_URL}/Patient?name={name_string}&gender={gender}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    data = response.json()
    if 'entry' in data:
        entry = data['entry']
        for item in entry:
            resource_id = item['resource']['id']
            given_name = f"{item['resource']['name'][0]['given'][0]}"
            family_name = f"{item['resource']['name'][0]['family']}"
            print(f"{resource_id} - {item['resource']['gender']} - {given_name} {family_name}")
    else:
        print('No results found')


def search_patient_where_address_contains(address_string):
    url = f'{BASE_URL}/Patient?address:contains={address_string}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    pprint(response.json())


def get_patient_name_where_address_contains(address_string):
    url = f'{BASE_URL}/Patient?address:contains={address_string}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    data = response.json()
    entry = data['entry']
    for item in entry:
        resource_id = item['resource']['id']
        given_name = f"{item['resource']['name'][0]['given'][0]}"
        family_name = f"{item['resource']['name'][0]['family']}"
        print(resource_id)
        print(given_name)
        print(family_name)
        print()


def get_patient_where_dob_equals(birth_date):
    url = f'{BASE_URL}/Patient?birthdate={birth_date}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    data = response.json()
    entry = data['entry']
    for item in entry:
        resource_id = item['resource']['id']
        given_name = f"{item['resource']['name'][0]['given'][0]}"
        family_name = f"{item['resource']['name'][0]['family']}"
        print(resource_id)
        print(given_name)
        print(family_name)
        print()


def get_patient_gender_where_dob_greater_than(birth_date):
    url = f'{BASE_URL}/Patient?birthdate=gt{birth_date}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    data = response.json()
    if 'entry' in data:
        print(f"Number of entries: {len(data['entry'])}")
        entry = data['entry']
        for item in entry:
            resource_id = item['resource']['id']
            print(f"{resource_id} - {item['resource']['gender']} - {item['resource']['birthDate']}")
    else:
        print('No results found')


def search_condition(patient_resource_id):
    url = f'{BASE_URL}/Condition?patient={patient_resource_id}'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    data = response.json()
    if 'entry' in data:
        print(f"Number of entries: {len(data['entry'])}")
        print()
        entry = data.get('entry')
        for item in entry:
            resource_type = item['resource']['resourceType']
            resource_id = item['resource']['id']
            code = item['resource']['code']['coding'][0]['code']
            print(f'Resource type: {resource_type}')
            print(f'Resource ID: {resource_id}')
            print(f'Code: {code}')
            print()

    else:
        print('No results found')


def search_observation(patient_resource_id):
    url = f'{BASE_URL}/Observation?patient={patient_resource_id}&code=http://loinc.org|85354-9'
    response = requests.get(url=url, headers=get_headers())
    print(response.url)
    if response.status_code == 200:
        data = response.json()
        if 'entry' in data:
            print(f"Number of entries: {len(data['entry'])}")
            print()
            entry = data.get('entry')
            for item in entry:
                pprint(item)
                resource_type = item['resource']['resourceType']
                resource_id = item['resource']['id']
                print(f'Resource type: {resource_type}')
                print(f'Resource ID: {resource_id}')
        else:
            print('No results found')
    else:
        print(f"Error when trying to access data: {response.status_code}")
        print(f"Error: {response.json()}")


if __name__ == '__main__':
    print()
    # get_fhir_patient(resource_id='9d035909-a26e-4271-ab8f-e57ca59d2286')
    # search_patient_by_name(name_string='Kuvalis')
    search_patient_by_name_gender(name_string='Kuvalis', gender='male')
    # search_patient_where_address_contains(address_string='West Springfield')
    # get_patient_name_where_address_contains(address_string='West Springfield')
    # get_patient_where_dob_equals(birth_date='1995-04-23')
    # get_patient_gender_where_dob_greater_than(birth_date='2010-01-01')
    # search_condition(patient_resource_id='985ac6ea-c3e8-4bd4-ae43-41683cb26135')
    # search_observation(patient_resource_id='985ac6ea-c3e8-4bd4-ae43-41683cb26135')
