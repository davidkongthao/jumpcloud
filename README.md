# JumpCloud Python API (Work in Progress)

Even though JumpCloud has their own Python library, there weren't any functionalities that would really fit my use-case, where I would had wanted to provision and update users from a provided .csv file, so I created this library. The library has two main functionalities so far:

- Creating users from a CSV file.
- Creating user groups from a CSV file and associating created users to those groups.

Other functionalities will come along later.

## Requirements: 
- Python 3.6+
- JumpCloud account and API key

## Getting Started
1. To get started, clone the repository
`git clone git@github.com:davidkongthao/jumpcloud.git`

2. cd into the cloned repository and initialize a virtual Python environment:
`python -m venv .`

3. Install the required pip packages:
`pip install -r requirements.txt`

4. cd into the `src` directory, and format a .csv file in the `files` directory, examples are given, ***All fields are required.***

5. Set an environment variable name ***JUMPCLOUD_API_KEY***, which you can set in a `.env` file in the src directory or you can run the following command on Mac or Linux:
`export JUMPCLOUD_API_KEY={YOUR_API_KEY_HERE}`	
or on Windows:
`set JUMPCLOUD_API_KEY={YOUR_API_KEY_HERE`

6. Pass in the names of the csv files that you have created in the `files` directory into the script in `main.py`:
```
def main():
	jc = JumpCloudAPI(api_key=JUMPCLOUD_API_KEY)
	jc.create_user_groups(group_file='groups.csv') # CSV file of Groups
	jc.create_users(user_file='users.csv') # CSV file of Users
	jc.update_group_membership(group_membership_file='group_membership.csv', group_mapping_file='group_mapping.json')
```
Then run the script with: 
`python main.py`


