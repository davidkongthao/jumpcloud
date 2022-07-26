import os
from jumpcloud import JumpCloudAPI
from dotenv import load_dotenv

load_dotenv()

JUMPCLOUD_API_KEY = os.environ.get("JUMPCLOUD_API_KEY")

def main():
    jc = JumpCloudAPI(api_key=JUMPCLOUD_API_KEY)
    jc.create_user_groups(group_file='groups.csv')
    jc.create_users(user_file='users.csv')
    jc.update_group_membership(group_membership_file='group_membership.csv', group_mapping_file='group_mapping.json')

if __name__ == '__main__':
    main()