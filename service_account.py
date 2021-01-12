"""
Prerequisites:
pip3 install --upgrade google-api-python-client  google-auth google-auth-httplib2
pip3 install oauth2client

Test:
gcloud auth activate-service-account terraform-test8@easyence-sandbox.iam.gserviceaccount.com   --key-file=/home/franck/terraform-test8-easyence-sandbox.json  --project=easyence-sandbox
bq ls --> to test the role "roles/bigquery.dataViewer"
gcloud auth login --> to authenticate with your gmail account
"""
from os.path import expanduser
from pprint import pprint
from googleapiclient import discovery,errors
from oauth2client.client import GoogleCredentials
from google.oauth2 import service_account
import googleapiclient.discovery
import base64
import json
import sys

HOME = expanduser("~")
credentials = GoogleCredentials.get_application_default()
list_email = []

def list_project(credentials):
    service = discovery.build('cloudresourcemanager', 'v1', credentials=credentials)
    request = service.projects().list()
    response = request.execute()
#    pprint(response.get('projects', []))
    return response.get('projects', [])
 
def manage_service_accounts(credentials,project_id):
    service = googleapiclient.discovery.build('iam', 'v1', credentials=credentials)
    pprint("Start with " + project_id + " Project")
    try:
        service_accounts = service.projects().serviceAccounts().list(
            name= 'projects/' + project_id).execute()
        for email in service_accounts['accounts']:
            list_email.append(email['email'])
        if str(service_acc + "@"+project['projectId'] + ".iam.gserviceaccount.com") in list_email:
            print (" [ALREADY EXIST]  Service account " + service_acc + " already exist for project " + project_id + "\n")
        else:
            create_service_account(credentials,project_id,service_acc)
        return service_accounts['accounts']
    except errors.HttpError as e:
        print("Project: " + project_id + " ---> Error status code : " + str(e.resp.status) + "\n")

def create_service_account(credentials,project_id, name):
    member = str("serviceAccount:"+service_acc+"@"+project_id+".iam.gserviceaccount.com")
    service = googleapiclient.discovery.build('iam', 'v1', credentials=credentials)

    service_account = service.projects().serviceAccounts().create(
        name='projects/' + project_id,
        body={
             'accountId': name,
             'serviceAccount': {
                 'displayName': service_acc,
                 'description': str("service account for "+service_acc)
             }
         }).execute()

    modify_policy_add_role(project_id, role, member)
    try:
        key = service.projects().serviceAccounts().keys().create(
            name='projects/-/serviceAccounts/' + service_account['email'], body={}
            ).execute()
    except HttpError as e:
        print("Create Project: " + project_id + " ---> Error status code : "+str(e.resp.status)+"\n") 
    print('Service Account key Created: ' + key['name'])
    key=base64.b64decode(key['privateKeyData'])
    key=json.loads(key)
    key=json.dumps(key, sort_keys=False, indent=4)
    with open(HOME+"/" + service_acc + "-" + project_id + ".json", 'w') as json_file:
        json_file.write(str(key))
    print("Service Account Created : "  + service_account['email'] + " for project " + project_id)
    print("Service Account Key file : " + str(HOME + "/" + service_acc + "-" + project_id + ".json"))
    return service_account

def modify_policy_add_role(project_id, role, member):
    """Adds a new role binding to a policy."""
    service = discovery.build('cloudresourcemanager', 'v1', credentials=credentials)
    policy = get_policy(service, project_id)

    binding = None
    for b in policy["bindings"]:
        if b["role"] == role:
            binding = b
            break
    if binding is not None:
        binding["members"].append(member)
    else:
        binding = {"role": role, "members": [member]}
        policy["bindings"].append(binding)

    set_policy(service, project_id, policy)

def get_policy(service, project_id, version=3):
    """Gets IAM policy for a project."""

    policy = service.projects().getIamPolicy(
            resource=project_id,
            body={"options": {"requestedPolicyVersion": version}},
        ).execute()
    return policy

def set_policy(crm_service, project_id, policy):
    """Sets IAM policy for a project."""

    policy = crm_service.projects().setIamPolicy(
        resource=project_id,
         body={"policy": policy}
         ).execute()
    return policy

# Main program
if __name__ == '__main__':
    if len(sys.argv) == 3:
        service_acc = sys.argv[1]        #"terraform-test3"
        role        = sys.argv[2]        #"roles/bigquery.dataViewer"
        print(" This Script Create Service Account for all Project and Generate Key File \n")
        print("[START] We have " + str(len(list_project(credentials))) + " Projects \n")
        for project in list_project(credentials):
            manage_service_accounts(credentials,project["projectId"])            
    else:
        print("\033[1;31;40m [ERROR] \033[1;37;40m The script needs 2 parameters: ")
        print("First parameter: service account name")
        print("Second parameter: role")
        print("Example: python3 service_account.py  terraform-test3 roles/bigquery.dataViewer ")