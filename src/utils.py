import os
import sys
import csv
import json
from datetime import datetime, timedelta

DEFAULT_EMAIL_DOMAIN = 'amplyr.com'
DEFAULT_USER_CSV_HEADERS = [
    'firstName', 'middleName', 'lastName','username', 
    'jobTitle', 'department', 'managerName', 'employeeId', 
    'streetAddress', 'city', 'state', 'postalCode', 
    'country', 'dateOfEmployment', 'isActive', 'dateTerminated',
    'employeeType', 'managerUsername', 'phoneNumber'
]
DEFAULT_GROUP_CSV_HEADERS = ['GroupName', 'Email', 'Description', 'GroupId']
DEFAULT_GROUP_MEMBERSHIP_CSV_HEADERS = ['username', 'memberOf']
DEFAULT_COMPANY_EMAIL_DOMAIN = 'amplyr.com'
DEFAULT_COMPANY = 'Amplyr LLC'
DEFAULT_MFA_EXCLUSION_TIMELINE = 3

def validate_csv_file(input_file: str):
    if input_file.split('.')[-1] != 'csv':
        sys.exit(f'{input_file} is not a valid .csv file.')
    if not os.path.isfile(input_file):
        sys.exit(f'{input_file} does not exist in the current directory.')

def validate_csv_headers(input_file: str, required_headers: list):
    with open(input_file, 'r') as csv_file:
        read_csv_file = csv.reader(csv_file, delimiter=',')
        headers = [x for x in read_csv_file][0]

        if len(headers) != len(required_headers):
            sys.exit(f'{input_file} is missing or has additional headers.')

        for header in headers:
            if header not in required_headers:
                sys.exit(f'{input_file} has an invalid header: {header}')

def validate_no_duplicate_id(input_id: str):
    ids = []
    if input_id in ids:
        sys.exit(f'The ID {input_id} has overlapping numbers.')
    ids.append(input_id)

def format_group_file(group_file: str) -> list:
    validate_csv_file(input_file=group_file)

    validate_csv_headers(
        input_file=group_file,
        required_headers=DEFAULT_GROUP_CSV_HEADERS
    )

    groups = []

    with open(group_file, 'r') as f:
        loaded_csv_file = csv.DictReader(f)
        groups = list(loaded_csv_file)
        for group in groups:
            for key in group:
                if group[key] is None:
                    sys.exit(f'{key} cannot be blank. The issue is at {group["GroupName"]}')

            group_id = group['GroupId']
            validate_no_duplicate_id(input_id=group_id)
    
    jumpcloud_group_data = [
        {
            'name': x['GroupName'],
            'email': x['Email'],
            'description': x['Description'],
            'attributes': {
                'property': {
                    'group_id': x['GroupId']
                }
            }
        }

        for x in groups
    ]

    return jumpcloud_group_data

def format_data(input_file: str) -> list:
    validate_csv_file(input_file=input_file)
    
    validate_csv_headers(
        input_file=input_file,
        required_headers=DEFAULT_USER_CSV_HEADERS
    )

    with open(input_file, 'r') as csv_file:
        usernames = []
        employee_ids = []
        index = 1

        loaded_csv_file = csv.DictReader(csv_file)
        users = list(loaded_csv_file)
        for user in users:
            first_name = user.get('firstName')
            last_name = user.get('lastName')
            employee_id = user.get('employeeId')
            username = user.get('username')
            index += 1
            for key in user:
                if key != 'middleName' and user[key] is None:
                    sys.exit(f'{key} cannot be blank. The issue is at {first_name} {last_name} | {username} on line {index}.')
                    
            if employee_id in employee_ids:
                sys.exit(f'The Employee ID {employee_id} on line {index} conflicts with another existing employee ID.')        

            if username in usernames:
                sys.exit(f'The username {username} on line {index} conflicts with another existing username.')
            
            employee_ids.append(employee_id)
            usernames.append(username)


        bulk_users = []

        for user in users:
            context = {
                'email': f'{user.get("username")}@{DEFAULT_COMPANY_EMAIL_DOMAIN}',
                'firstname': user.get('firstName'),
                'lastname': user.get('lastName'),
                'username': user.get('username')
            }
            bulk_users.append(context)
        
        user_informations = []

        for user in users:
            context = {}
            context['activated'] = True
            context['account_locked'] = False
            context['state'] = 'ACTIVATED'

            if user.get('isActive') == 'FALSE':
                context['activated'] = False
                context['account_locked'] = True
                context['state'] = 'SUSPENDED'

            context['addresses'] = [
                {
                    'country': user.get('country'),
                    'extendedAddress': '',
                    'locality': user.get('city'),
                    'poBox': '',
                    'postalCode': user.get('postalCode'),
                    'region': user.get('state'),
                    'streetAddress': user.get('streetAddress'),
                    'type': 'work'
                },
                {
                    'country': user.get('country'),
                    'extendedAddress': '',
                    'locality': user.get('city'),
                    'poBox': '',
                    'postalCode': user.get('postalCode'),
                    'region': user.get('state'),
                    'streetAddress': user.get('streetAddress'),
                    'type': 'home'
                }
            ]

            context['attributes'] = [{
                'name': 'dateOfEmployment',
                'value': f'{user.get("dateOfEmployment")}'
            }]

            future_date = datetime.now() + timedelta(days=DEFAULT_MFA_EXCLUSION_TIMELINE)

            context['mfa'] = {
                'configured': True,
                'exclusion': True,
                'exclusionUntil': future_date.isoformat()
            }
            context['company'] = DEFAULT_COMPANY
            context['department'] = user.get('department')
            context['employeeIdentifier'] = f'{user.get("employeeId")}'
            context['firstname'] = user.get('firstName')
            context['jobTitle'] = user.get('jobTitle')
            context['lastname'] = user.get('lastName')
            context['manager'] = user.get('managerUsername')
            context['employeeType'] = user.get('employeeType')
            context['middlename'] = user.get('middleName')
            context['username'] = user.get('username')
            context['displayname'] = f'{user.get("firstName")} {user.get("lastName")}'
            context['enable_user_portal_multifactor'] = True
            context['disableDeviceMaxLoginAttempts'] = False
            context['phoneNumbers'] = [
                {
                    'type': 'work',
                    'number': user.get('phoneNumber')
                }
            ]
            user_informations.append(context)
        
        return [bulk_users, user_informations]

def format_system_user_data(data: dict) -> list:
    users = []
    for user in data:
        context = {
            'username': user.get('username'),
            'user_id': user.get('id'),
            'first_name': user.get('firstname'),
            'last_name': user.get('lastname'),
            'email': user.get('email')
        }
        users.append(context)
    return users

def format_user_group_mapping_data(group_membership_file: str, group_mapping_file: str) -> list:
    group_membership_file_path = os.path.join(os.getcwd(), f'files/{group_membership_file}')
    validate_csv_file(input_file=group_membership_file_path)
    group_mapping_file_path = os.path.join(os.getcwd(), f'files/{group_mapping_file}')

    if group_mapping_file.split('.')[-1] != 'json':
        sys.exit(f'{group_mapping_file} is not a valid json file.')
    
    if not os.path.isfile(group_mapping_file_path):
        sys.exit(f'{group_mapping_file} is not in the current directory.')
    
    validate_csv_headers(
        input_file=group_membership_file_path,
        required_headers=DEFAULT_GROUP_MEMBERSHIP_CSV_HEADERS
    )

    opened_mapping_data = open(group_mapping_file_path)
    mapped_data_groups = json.load(opened_mapping_data)['groups']

    data = []

    with open(group_membership_file_path, 'r') as csv_file:
        loaded_csv_file = csv.DictReader(csv_file)
        users = list(loaded_csv_file)

        for user in users:
            groups = []
            context = {
                'username': user.get('username')
            }
            if user['memberOf'] == 'ALL':
                for group in mapped_data_groups:
                    groups.append(group['value'])
            
            member_of = user['memberOf'].split(',')
            for item in member_of:
                for group in mapped_data_groups:
                    if item == group['input']:
                        groups.append(group['value'])

            context['groups'] = [ x.replace(' ', '+') for x in groups ]
            context['groups'].append('All+Users')
            data.append(context)

    return data