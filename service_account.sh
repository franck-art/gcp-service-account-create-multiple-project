#!/bin/bash

# NB: Before running this script, make sure you have the necessary rights in all GCP projects
# Objectifs:
# - List of all projects GCP
# - check if service account exist for each project
# - Create a service account of all projects

# Variables
serv_acc="$1"               # service account name of all projects  ---> Ex: terraform-bigquery
role="$2"                   # Roles link with service account  ----> Ex: bigquery.dataViewer
projects=$(gcloud projects list | tail -n+2 | awk '{print $1}')             # List of projects
ls_projects=$(echo "$projects" | wc -w)

# Functions definitions
function service_acc_create() {
  gcloud --project "$1" iam service-accounts create "${serv_acc}"\
    --description="${role} automation" \
    --display-name="${role}" &&\
  echo -e "\033[32m [OK] \033[0m Service Account Created" &&\
  gcloud projects add-iam-policy-binding "$1" --member=serviceAccount:"${serv_acc}"@"${1}".iam.gserviceaccount.com --role=roles/"${role}" &&\
  echo -e "\033[32m [OK] \033[0m Service Account Owner Role Granted" &&\
  gcloud --project "$1" iam service-accounts keys create ~/"${1}"-"${role}".json \
    --iam-account "${serv_acc}"@"${1}".iam.gserviceaccount.com &&\
  echo -e "\033[32m [OK] \033[0m Service Account Key Created: \$HOME/${1}-${role}.json" &&\
  echo -e "\033[33m Don't Forget Adding serviceAccount:${serv_acc}@${1}.iam.gserviceaccount.com to the terraform project.\033[0m"
  EXCODE=$?
  if [ "$EXCODE" == "0" ]; then
    echo "[Done]"
  else
    echo -e "\033[31m Error Occured, Now Rolling Back \033[0m"
    gcloud --project "$1" -q iam service-accounts delete "${serv_acc}"@"${1}".iam.gserviceaccount.com
  fi
}

# Start of main program
if [ "$#" -eq  2 ]; then 
pos_project=0
echo -e "\033[34m [START] \033[0m We have ${ls_projects} Projects"
for project in $projects
do
 i=0
 pos_project=$((pos_project+1))
 echo -e "\033[34m [START][${pos_project}] \033[0m  Start with ${project} Project"
 nb_service=$(gcloud --project "$project"  iam service-accounts list | tail -n+2 | wc -l)
    if [ "$nb_service" -eq  0 ]; then
      service_acc_create "$project"
    else
      ls_service=$(gcloud --project "$project"  iam service-accounts list | tail -n+2 | cut -d '@' -f1 | awk '{print $NF}')
      nb=$(echo "$ls_service" | wc -w)
        for service_acc in $ls_service
        do
           if [ "$service_acc" != "$serv_acc" ]; then
              i=$((i+1))
                if [ "$i" -eq "$nb" ]; then
                    service_acc_create "$project"
                fi
           else
             echo -e "\033[31m [ALREADY EXIST] \033[0m A service account ${serv_acc} already exist for project ${project} "
             break
           fi
        done
    fi
done
else
echo -e "\033[31m [NOTE]: Put two parameters when you call the script \033[0m"
echo -e "First parameter: Service Account Name. Ex: terraform-bigquery"
echo -e "Second parameter: Role link with service account. Ex: bigquery.dataViewer"
fi