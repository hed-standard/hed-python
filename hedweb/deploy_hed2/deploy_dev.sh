#!/bin/bash

# deploy.sh - A script used to build and deploy a docker container for the HEDTools webinterface validator

##### Constants

ROOT_DIR="${PWD}"
IMAGE_NAME="hedtools-validation:latest"
CONTAINER_NAME="hedtools-validation"
# GIT_REPO_URL="https://github.com/VisLab/hed-python"
GIT_REPO_URL="https://github.com/hed-standard/hed-python"
GIT_DIR="${ROOT_DIR}/hed-python"
GIT_REPO_BRANCH="master"
HOST_PORT=33000;
CONTAINER_PORT=80;

DEPLOY_DIR="${ROOT_DIR}/hed-python/hedweb/deploy_hed2"
CODE_DEPLOY_DIR="${DEPLOY_DIR}/hedtools"
CONFIG_FILE="${ROOT_DIR}/config.py"
WSGI_FILE="${DEPLOY_DIR}/webinterface.wsgi"
DOCKER_FILE="${DEPLOY_DIR}/Dockerfile_dev"
DOCKER_FILE_DEPLOY="${DEPLOY_DIR}/Dockerfile"
WEBINTERFACE_CODE_DIR="${ROOT_DIR}/hed-python/hedweb/hed"
VALIDATOR_CODE_DIR="${ROOT_DIR}/hed-python/hedvalidation/hed"

##### Functions

clone_github_repo(){
echo Cloning hed-python repo in directory  "${ROOT_DIR}" ...
git clone "${GIT_REPO_URL}" -b "${GIT_REPO_BRANCH}"
}

create_web_directory()
{
echo Creating the web directory...
echo Currently in "${PWD}" ... root directory is "${ROOT_DIR}"
echo Making the code  deploy directory "${CODE_DEPLOY_DIR}" ...
mkdir "${CODE_DEPLOY_DIR}"

echo Copying "${CONFIG_FILE}" to "${CODE_DEPLOY_DIR}" ...
cp "${CONFIG_FILE}" "${CODE_DEPLOY_DIR}"

echo Copying "${WSGI_FILE}" to "${CODE_DEPLOY_DIR}" ...
cp "${WSGI_FILE}" "${CODE_DEPLOY_DIR}"

echo Copying "${DOCKER_FILE}" to "${DOCKER_FILE_DEPLOY}" ...
cp "${DOCKER_FILE}" "${DOCKER_FILE_DEPLOY}"

echo Copying "${WEBINTERFACE_CODE_DIR}" to "${CODE_DEPLOY_DIR}" ...
cp -r "${WEBINTERFACE_CODE_DIR}" "${CODE_DEPLOY_DIR}"

echo Copying "${VALIDATOR_CODE_DIR}" to "${CODE_DEPLOY_DIR}" ...
cp -r "${VALIDATOR_CODE_DIR}" "${CODE_DEPLOY_DIR}"
}

switch_to_web_directory()
{
echo Switching to web directory "${DEPLOY_DIR}" ...
cd "${DEPLOY_DIR}"
}

build_new_container()
{
echo Building new container "${IMAGE_NAME}" ...
docker build -t "${IMAGE_NAME}" .
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
rm -rf "${GIT_DIR}"
rm -rf "${GIT_HED_DIR}"
cd "${ROOT_DIR}" || error_exit Failed to clean up
}

error_exit()
{
	echo "$1" 1>&2
	exit 1
}

##### Main
if [ -z "$1" ]; then
echo No branch specified... Using master branch
else
echo Branch specified... Using "$1" branch
GIT_REPO_BRANCH="$1"
fi
clone_github_repo || error_exit "Cannot clone repo ${GIT_REPO_URL} branch ${GIT_REPO_BRANCH}"
create_web_directory
switch_to_web_directory
build_new_container
delete_old_container
run_new_container
cleanup_directory
