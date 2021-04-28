#!/bin/bash

# deploy.sh - A script used to build and deploy a docker container for the HEDTools online validator

##### Constants

ROOT_DIR=${PWD}
IMAGE_NAME="hedtools:latest"
CONTAINER_NAME="hedtools"
GIT_REPO_URL="https://github.com/hed-standard/hed-python"
GIT_DIR="${PWD}/hed-python"
GIT_REPO_BRANCH="master"
HOST_PORT=33000
CONTAINER_PORT=80

DEPLOY_DIR="hed-python/webtools/deploy_hed"
CODE_DEPLOY_DIR="${DEPLOY_DIR}/hedtools"
CONFIG_FILE="${ROOT_DIR}/config.py"
WSGI_FILE="${DEPLOY_DIR}/web.wsgi"
WEB_CODE_DIR="hed-python/webtools/hedweb"
VALIDATOR_CODE_DIR="hed-python/hedtools/hed"

##### Functions

clone_github_repo(){
echo Cloning repo ...
git clone $GIT_REPO_URL -b $GIT_REPO_BRANCH
}

create_web_directory()
{
echo Creating hedweb directory...
mkdir "${CODE_DEPLOY_DIR}"
cp "${CONFIG_FILE}" "${CODE_DEPLOY_DIR}"
cp ${WSGI_FILE} "${CODE_DEPLOY_DIR}"
cp -r "${WEB_CODE_DIR}" "${CODE_DEPLOY_DIR}"
cp -r "${VALIDATOR_CODE_DIR}" "${CODE_DEPLOY_DIR}"
}

switch_to_web_directory()
{
echo Switching to hedweb directory...
cd "${DEPLOY_DIR}" || error_exit "Cannot access $DEPLOY_DIR"
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
docker run --restart=always --name $CONTAINER_NAME -d -p 127.0.0.1:$HOST_PORT:$CONTAINER_PORT $IMAGE_NAME
}

cleanup_directory()
{
echo Cleaning up directory...
rm -rf "${GIT_DIR}"
cd "${ROOT_DIR}" || error_exit "Cannot clean up directories"
}

error_exit()
{
	echo "$1" 1>&2
	exit 1
}

output_paths()
{
echo "The relevant deployment information is:"
echo "Root directory: ${ROOT_DIR}"
echo "Docker image name: $IMAGE_NAME"
echo "Docker image name: ${IMAGE_NAME}"
echo "Docker container name: ${CONTAINER_NAME}"
echo "Git repo: ${GIT_REPO_URL}"
echo "Local repository: ${GIT_DIR}"
echo "Host port: ${HOST_PORT}"
echo "Container port: ${CONTAINER_PORT}"
echo "Local deployment directory: ${DEPLOY_DIR}"
echo "Local code deployment directory: ${CODE_DEPLOY_DIR}"
echo "Configuration file: ${CONFIG_FILE}"
echo "WSGI file: ${WSGI_FILE}"
echo "Local web code directory: ${WEB_CODE_DIR}"
echo "Local validator code directory: ${VALIDATOR_CODE_DIR}"
}


##### Main
echo "Starting...."
output_paths
echo "....."
if [ -z "$1" ]; then
echo No branch specified... Using master branch
else
echo Branch specified... Using "$1" branch
GIT_REPO_BRANCH="$1"
fi
clone_github_repo || error_exit "Cannot clone repo $GIT_REPO_URL branch $GIT_REPO_BRANCH"
create_web_directory
switch_to_web_directory
build_new_container
delete_old_container
run_new_container
cleanup_directory
