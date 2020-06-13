#!/bin/bash

# deploy.sh - A script to install hedemailer on a server.  Note this will NOT install a mail utility if you don't have one.  

##### Constants

ROOT_DIR=${PWD}
GIT_DIR="${PWD}/hed-python"
GIT_REPO_URL="https://github.com/hed-standard/hed-python"
GIT_REPO_BRANCH="master"
SERVER_CONFIG_DIR=${ROOT_DIR}
CONFIG_FILE="${SERVER_CONFIG_DIR}/config.py"
WSGI_FILE="${SERVER_CONFIG_DIR}/hedemailer.wsgi"


HEDEMAILER_CODE_DIR="$GIT_DIR/hedemailer"
CONVERSION_CODE_DIR="$GIT_DIR/hedconversion/hedconversion"
ENV_DIR="${PWD}/hedemailer_env"

SERVER_CODE_DIR="/var/www/gollum/hedemailer"
SERVER_ENV_DIR="/var/www/gollum/env"

##### Functions

clone_github_repo(){
echo Cloning repo ... 
git clone $GIT_REPO_URL -b $GIT_REPO_BRANCH
}

create_virtual_env() {
echo Creating virtual env...
virtualenv -p python3 $ENV_DIR
source $ENV_DIR/bin/activate
pip3 install -r hed-python/hedemailer/deploy/requirements.txt
}

cleanup_old_server_data() {
echo Cleaning up old server data...
sudo rm -r $SERVER_CODE_DIR
sudo rm -r $SERVER_ENV_DIR
sudo rm -r /var/www/gollum/
sudo mkdir /var/www/gollum
}

move_env_to_server_and_modify() {
echo Moving to server...
sudo cp -r $GIT_DIR/hedemailer/ $SERVER_CODE_DIR
sudo cp -r $GIT_DIR/hedconversion/hedconversion/ $SERVER_CODE_DIR/hedconversion/
sudo cp -r $ENV_DIR $SERVER_ENV_DIR
sudo sed -i -e "s|VIRTUAL_ENV=\"$ENV_DIR\"|VIRTUAL_ENV=\"$SERVER_ENV_DIR\"|g" $SERVER_ENV_DIR/bin/activate
}

move_config_to_server() {
echo Moving config to server...
sudo cp $CONFIG_FILE $SERVER_CODE_DIR/
sudo cp $WSGI_FILE $SERVER_CODE_DIR/
}
cleanup_directory()
{
echo Cleaning up directory...
rm -rf $GIT_DIR
rm -rf $ENV_DIR
cd $ROOT_DIR
}

restart_server() {
sudo systemctl restart apache2
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
create_virtual_env
cleanup_old_server_data
move_env_to_server_and_modify
move_config_to_server
restart_server
cleanup_directory
