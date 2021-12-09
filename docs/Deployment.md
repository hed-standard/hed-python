Instructions for HED docker deployment
These instructions are for setting up the HED online tools on a Ubuntu 20 server running Apache 2 and Docker.

Table of contents
Instructions for HED docker deployment	1
1. Steps for installation of system software	2
1.1  Preliminaries	2
1.1.1 Verify Ubuntu 20 is installed and everything is up to date	2
1.1.2 Install Apache	2
1.1.3 Install ssh if not there	2
1.1.4 Make sure that firewall allows ssh and apache	2
1.1.5 Make sure required services are up and running	2
1.1.6 Make sure python 3 is installed on the system:	2
1.1.7 Upgrade pip to the latest version	3
1.2 Installing Docker	3
1.2.1 Install the prerequisites for Docker	3
1.2.2 Add dockers official GPG key	3
1.2.3 Add docker repository to APT sources	3
1.2.4 Set up docker through Apache	3
1.2.5  Create a hedbasic.conf text file	3
1.2.6 Set apache’s configuration for HED docker	4
1.2.7 Conversion from windows to linux files	4
2. Deploying hed docker web	5
2.1 Check Docker status	5
2.2  Deploy the hed containers on your server	5
2.2.1  Clone the python repository to the local machine	6
2.2.2   Upload setup directories to server	6
2.2.3   Deploy hed	6

1. Steps for installation of system software 
1.1  Preliminaries
1.1.1 Verify Ubuntu 20 is installed and everything is up to date
sudo apt-get update
sudo apt-get dist-upgrade	
sudo apt autoremove
1.1.2 Make sure that 127.0.0.1 is localhost
These instructions assume that we are using 127.0.0.1 as local host and that it is explicitly set in the internal hosts table.  Add the following line to /etc/hosts:

		127.0.0.1	localhost
1.1.3 Install Apache
Install Apache 2 using:
      	sudo apt install apache2

Edit the /etc/apache2/apache2.conf file and put the following line at the bottom:
		ServerName server_domain_or_IP

Restart the apache server:
		sudo systemctl restart apache2

Check to make sure configuration is okay:
		sudo apache2ctrl configtest

Check applications (should have Apache, Apache Full, Apache Secure, CUPS, OpenSSH):
		sudo ufw app list

Check ports (should have ports 80, 443/tcp):
             sudo ufw app info “Apache Full”
		 sudo ufw allow in “Apache full”

Check that /etc/apache2/apache2.conf is properly set up.  You need to make sure that the following is uncommented:

<Directory /var/www/>
        		Options Indexes FollowSymLinks
        		AllowOverride None
        		Require all granted
</Directory>

You will also need to set the ServerName to have the appropriate external IP address or actual hostname:

		ServerName xxx.xxx.xxx.xxx

1.1.4 Install ssh if not there
Install ssh:
		sudo apt install ssh

Then edit /etc/ssh/sshd_config so that it contains:
Match group sftp
ChrootDirectory /home
X11Forwarding no
AllowTcpForwarding no
ForceCommand internal-sftp

1.1.5 Make sure that firewall allows ssh and apache
sudo ufw allow ssh
sudo ufw allow 'Apache'
sudo ufw enable
sudo ufw app list
sudo ufw status
1.1.6 Make sure required services are up and running
sudo service --status-all
Check that the following services are on:  ssh, apache, ufw as well as the usual suspects. 
1.1.7 Make sure python 3 is installed on the system:
          		 python3 -V
1.1.8 Upgrade pip to the latest version
sudo apt update
     		sudo apt install python3-pip
     		pip3 --version
     		sudo pip3 install --upgrade pip
1.2 Installing Docker
1.2.1 Install the prerequisites for Docker
sudo apt-get install apt-transport-https
sudo apt-get install ca-certificates
sudo apt-get install curl
sudo apt-get install gnupg-agent
sudo apt-get install software-properties-common
1.2.2 Add dockers official GPG key
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
1.2.3 Add docker repository to APT sources
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
apt-cache policy docker-ce

1.2.4 Set up docker through Apache
sudo apt install docker docker-compose
sudo systemctl enable --now docker

sudo apt-get install docker-ce 
sudo apt-get install docker-ce-cli 
sudo apt-get install containerd.io

1.2.5 Create a hedbasic.conf text file
<VirtualHost *:80>
    			ServerName 127.0.0.1
    			ProxyPreserveHost On
    			ServerAdmin kay.robbins@utsa.edu
    			DocumentRoot /var/www/html
    			ErrorLog ${APACHE_LOG_DIR}/error.log
    			CustomLog ${APACHE_LOG_DIR}/access.log combined

        		<Directory /var/www/html>
            		Options -Indexes
        			AllowOverride None
            		Order allow,deny
            		allow from all
        		</Directory>

    			# This is the docker container for hed.
    			<Proxy>
    				Allow from 127.0.0.1
    			</Proxy>
        		ProxyPass /hed http://127.0.0.1:33000/hed
        		ProxyPassReverse /hed http://127.0.0.1:33000/hed 
</VirtualHost>
1.2.6 Set apache’s configuration for HED docker
sudo cp hedbasic.conf /etc/apache2/sites-enabled/
sudo cp hedbasic.conf /etc/apache2/sites-available/
sudo service apache2 restart

You should also delete 000-default.conf from sites-enabled and sites-available. If you get an error trying to start apache try:
sudo systemctl status apache2.service
If the error is on that it isn’t recognizing the Proxy command then do:
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod proxy_balancer
sudo a2enmod lbmethod_byrequests

1.2.7 Convert scripts from windows to linux file endings as needed
If you are working from a windows machine and getting error messages, you may be using an editor that uses windows line endings rather than Linux.  You might have to 
convert the deploy.sh and config.py files in each of the installations.  First install dos2unix:
           		sudo apt-get install -y dos2unix
To convert a file from windows line endings to linux in place:
     		dos2unix -k filename
2. Deploying hed docker web
We are assuming that you are on a local machine and installing the HED containers on a remote machine (the server). These instructions assume that you have done all of the previous installations from section 1 and that docker and the apache web server are running on the server.  Change to a working directory on your 
2.1 Check Docker status
To see what containers are running:
sudo docker ps
To see what images are running:
sudo docker images
You might want to get rid of existing containers.  To stop a container and remove it, use kill and rm with the container ID:
      	sudo docker kill 9c1798b8fc3f
      	sudo docker rm 9c1798b8fc3f
 
Use rmi with the image ID:
      	sudo docker rmi  5be6d36f77ee
If there is an error in deploying docker, check the logs:
 	docker logs --follow 5be6d36f77ee

To clear out all docker images on the server:
		sudo docker system prune -a

List all the docker images:
		sudo docker images -a
2.2  Deploy the hed container on your server
The instructions assume that you have a current copy of the hed-python repository on your local machine and that you are setting up docker on a server.  You are taking some information from a local version of the hed-python repository. You are doing the deployment from the hed_deploy directory in your home directory on the server.
2.2.1  Clone the python repository to the local machine 
git clone https://github.com/hed-standard/hed-python      
2.2.2   Upload setup directories to server
SSH into the server and upload the following directory to your home directory on the server:
hed-python/hedweb/deploy_hed

2.2.3   Deploy hed
Upload the deploy_hed directory in your home directory on the server and deploy:

          	cd ~/deploy_hed
          	sudo bash deploy.sh
If the script fails you might have to make sure that you have linux end of lines:
sudo apt-get install -y dos2unix.
     	dos2unix -k config.py
     	dos2unix -k deploy.sh
Now make sure that the service is running by accessing it in your web browser using:
          		http://myserver/hed
If it fails you will need to examine the docker log by using:
          		docker logs --follow 5be6d36f77ee
where the 5be6d36f77ee should be replaced by the container ID obtained from:
     		sudo docker ps
To get stop a running container type:
sudo docker stop 5be6d36f77ee
To copy the current directory structure of a docker container into a local directory for examination:
sudo docker cp 5be6d36f77ee:/ ./test
Other use
2.3  Testing that things are working on the deployed server
For the purposes of this test we assume that the host has IP address xxx.xxx.xxx.xxx and has all of the above setup done for an apache  web server running on port 80.  A browser request to:

	http://xxx.xxx.xxx.xxx/hed

should go directly to the hed website.  If everything is set up correctly a request to http://xxx.xxx.xxx.xxx:33000/hed should fail.  Our setup assumes that the docker container is accepting requests from localhost port 33000 and sends them to its internal web server running on port 80.  To check that docker thinks this is the setup, you should see the following (some columns have been omitted) when you do sudo docker ps:

CONTAINER ID   IMAGE               PORTS                      NAMES
4826a87fd812   hedtools:latest     127.0.0.1:33000->80/tcp    hedtools


2.4  Logs of interest
The Apache logs can be found at /var/log/apache2/error.log and /var/log/apache2/access.log.

The docker log can be found by doing:

		sudo docker logs hedtools


3.0. Local Docker Windows

docker run -d -p 80:80 docker/getting-started


4.0 Other issues:
https://docs.docker.com/engine/install/linux-postinstall/

sudo groupadd docker
o create the docker group and add your user:
Create the docker group.
$ sudo groupadd docker
 
Add your user to the docker group.
$ sudo usermod -aG docker $USER
 
Log out and log back in so that your group membership is re-evaluated.
If testing on a virtual machine, it may be necessary to restart the virtual machine for changes to take effect.
On a desktop Linux environment such as X Windows, log out of your session completely and then log back in.
On Linux, you can also run the following command to activate the changes to groups:
$ newgrp docker
sudo chmod 666 /var/run/docker.sock


