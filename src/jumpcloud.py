import os
import sys
import requests
import json
from utils import format_data, format_group_file, format_system_user_data, format_user_group_mapping_data

class JumpCloudAPI:

    """
    The JumpCloud class provides the functionality to query and 
    manage the objects within a JumpCloud organization.

    An JumpCloud API Key is required to initialize the class, and
    additionally, a Base API URL and API Version can be passed in.

    """

    def __init__(self, api_key: str, base_api_url: str = 'https://console.jumpcloud.com/api', api_version: str = 'v2'):
        self.headers = {
            'x-api-key': api_key
        }
        self.base_api_url = base_api_url
        self.api_url = f'{base_api_url}/{api_version}'

    def request(self, url: str):
        try:
            response = requests.get(url, headers=self.headers)
        except Exception as e:
            sys.exit(f'{e}')

        if response.status_code == 404:
            sys.exit(f'Request failed.')
        return response

    def obtain_organizations(self):
        url = f'{self.base_api_url}/organizations/'
        response = self.request(url=url)
        return json.loads(response.text)
    
    def obtain_organization_ids(self):
        data = self.obtain_organizations()
        try: 
            return [ { 'id': x['id'], 'name': x['displayName'] } for x in data['results'] ]
        except KeyError:
            sys.exit(f'Results from JumpCloud have either been updated or malformed. Please test the response to {self.base_api_url}/organizations/')
    
    def list_all_directories(self):
        url = f'{self.api_url}/directories'
        response = self.request(url=url)
        return json.loads(response.text)
    
    def list_all_gsuite_directories(self):
        data = self.list_all_directories()
        try:
            return [ { 'id': x['id'], 'name': x['name'] } for x in data if x['type'] == 'g_suite' ]
        except KeyError:
            sys.exit(f'Malformed response from JumpCloud for GSuite lookups.')    
    
    def create_user_groups(self, group_file: str):
        url = f'{self.api_url}/usergroups'
        file_path = os.path.join(os.getcwd(), f'files/{group_file}')
        groups = format_group_file(group_file=file_path)
        for group in groups:
            response = requests.post(url, json=group, headers=self.headers)
            if response.status_code == 201:
                print(f'Successfully import {group["name"]} into JumpCloud.')

    def list_groups(self):
        url = f'{self.api_url}/groups'
        response = self.request(url=url)
        return json.loads(response.text)

    def list_system_users(self, limit: int = 100):
        url = f'{self.base_api_url}/systemusers'
        query_string = {
            "limit": limit
        }
        response = requests.get(url, headers=self.headers, params=query_string)
        if response.status_code == 200:
            return format_system_user_data(data=json.loads(response.text)['results'])
        else:
            sys.exit('Failed to query system users in JumpCloud.')

    def create_bulk_users(self, data: list):
        url = f'{self.api_url}/bulk/users'
        headers = self.headers
        headers.update({'creation-source': 'jumpcloud:bulk'})
        headers.update({'content-type': 'application/json'})
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print(f'Successfully imported {len(data)} users.')
        else:
            sys.exit(response.text)

    def create_users(self, user_file: str):
        file_path = os.path.join(os.getcwd(), f'files/{user_file}')
        data = format_data(input_file=file_path)
        self.create_bulk_users(data=data[0])
        self.update_users(data=data[1])
    
    def get_user_id(self, username: str):
        url = f'{self.base_api_url}/systemusers'
        query_params = {
            'filter': f'username:$eq:{username}'
        }
        user_query = requests.get(url, headers=self.headers, params=query_params)
        if user_query.status_code == 200:
            total_count = json.loads(user_query.text)['totalCount']
            if total_count == 0:
                sys.exit(f'No results found for {username}')
            return json.loads(user_query.text)['results'][0].get('id')
    
    def get_group_id(self, group_name: str):
        url = f'{self.api_url}/usergroups'
        query_url = f'{url}?filter=name:eq:{group_name}'
        response = requests.get(query_url, headers=self.headers)
        if response.status_code == 200:
            return json.loads(response.text)[0].get('id')

    def get_system_user(self, user_id: str):
        url = f'{self.base_api_url}/systemusers/{user_id}'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return json.loads(response.text)['username']

    def add_group_members(self, user_id: str, group_id: str):
        url = f'{self.api_url}/usergroups/{group_id}/members'

        payload = {
            'id': user_id,
            'op': 'add',
            'type': 'user'
        }

        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 204:
            print(f'Successfully added user {user_id} to group {group_id}.')

    def update_group_membership(self, group_membership_file: str, group_mapping_file: str):
        users = format_user_group_mapping_data(group_membership_file=group_membership_file, group_mapping_file=group_mapping_file)
        for user in users:
            user_id = self.get_user_id(username=user['username'])
            for group in user['groups']:
                group_id = self.get_group_id(group_name=group)
                self.add_group_members(user_id=user_id, group_id=group_id)

    def update_users(self, data: list):
        url = f'{self.base_api_url}/systemusers'
        g_suite_id = self.list_all_directories()[0].get('id')
        for user in data:
            username = user.get('username')
            manager_username = user.get('manager')
            if manager_username != "":
                query_params = {
                    'filter': f'username:$eq:{manager_username}'
                }
                manager_user_query = requests.get(url, headers=self.headers, params=query_params)
                if manager_user_query.status_code == 200:
                    manager_id = json.loads(manager_user_query.text)['results'][0].get('id')
                    user['manager'] = manager_id
            else:
                user.pop('manager')
            
            query_params = {
                'filter': f'username:$eq:{username}'
            }
            user_query = requests.get(url, headers=self.headers, params=query_params)
            if user_query.status_code == 200:
                user_id = json.loads(user_query.text)['results'][0].get('id')                             
                query_url = f'{url}/{user_id}'

            response = requests.put(query_url, json=user, headers=self.headers)
            username = user.get('username')
            if response.status_code == 200:
                print(f'Successfully updated {username} in JumpCloud.')
                g_suite_url = f'{self.api_url}/gsuites/{g_suite_id}/associations'
                g_suite_data = {
                    'id': user_id,
                    'op': 'add',
                    'type': 'user'
                }
                g_suite_request = requests.post(g_suite_url, json=g_suite_data, headers=self.headers)
                if g_suite_request.status_code == 204:
                    print(f'Updated {username} in GSuite.')
                
            elif response.status_code == 401:
                print(response.text)
    
    def list_applications(self):
        pass