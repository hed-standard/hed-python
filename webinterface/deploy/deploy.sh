#!/bin/bash

# deploy.sh - A script used to build and deploy a docker container for the HEDTools web validator

##### Constants

ROOT_DIR=${PWD}
GIT_DIR="${PWD}/hed-python"
IMAGE_NAME="hedtools-validation:latest"
CONTAINER_NAME="hedtools-validation"
GIT_REPO_URL="https://github.com/hed-standard/hed-python"
GIT_REPO_BRANCH="master"
HOST_PORT=33000;
CONTAINER_PORT=80;
DEPLOY_DIR="hed-python/webinterface/deploy"
CODE_DEPLOY_DIR="${DEPLOY_DIR}/hedtools"
CONFIG_FILE="${ROOT_DIR}/config.py"
WSGI_FILE="${DEPLOY_DIR}/webinterface.wsgi"
WEBINTERFACE_CODE_DIR="hed-python/webinterface/webinterface"
VALIDATOR_CODE_DIR="hed-python/hedvalidation/hedvalidation"

GIT_HED_DIR="${PWD}/hed-specification"
GIT_HED_REPO_URL="https://github.com/hed-standard/hed-specification"
GIT_HED_REPO_FOLDER="hedxml"

##### Functions

clone_github_repo(){
echo Cloning repo ...
git clone $GIT_REPO_URL -b $GIT_REPO_BRANCH
}

clone_hed_github_repo(){
echo Cloning HED repo ...
git clone $GIT_HED_REPO_URL
}

create_web_directory()
{
echo Creating web directory...
mkdir $CODE_DEPLOY_DIR
cp $CONFIG_FILE $CODE_DEPLOY_DIR
cp $WSGI_FILE $CODE_DEPLOY_DIR
cp -r $WEBINTERFACE_CODE_DIR $CODE_DEPLOY_DIR
cp -r $VALIDATOR_CODE_DIR $CODE_DEPLOY_DIR
cp -r $GIT_HED_DIR $CODE_DEPLOY_DIR
}
switch_to_web_directory()
{
echo Switching to web directory...
cd $DEPLOY_DIR
}
build_new_container()
{
echo Building new container...
docker build -t $IMAGE_NAME .
}

delete_old_container()
{
echo Deleting old container...
docker rm -f $CONTAINER_NAME
}

run_new_container()
{
echo Running new container...
docker run --restart=always --name $CONTAINER_NAME -d -p $HOST_PORT:$CONTAINER_PORT $IMAGE_NAME
}

cleanup_directory()
{
echo Cleaning up directory...
rm -rf $GIT_DIR
rm -rf $GIT_HED_DIR
cd $ROOT_DIR
}

error_exit()
{
	echo "$1" 1>&2
	exit 1
}

##### Main
if [ -z $1 ]; then
echo No branch specified... Using master branch
else
echo Branch specified... Using $1 branch
GIT_REPO_BRANCH=$1
fi
clone_github_repo || error_exit "Cannot clone repo $GIT_REPO_URL branch $GIT_REPO_BRANCH"
clone_hed_github_repo || error_exit "Cannot clone repo $GIT_HED_REPO_URL"
create_web_directory
switch_to_web_directory
build_new_container
delete_old_container
run_new_container
cleanup_directory
