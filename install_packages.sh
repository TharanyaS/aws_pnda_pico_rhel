if [ -f /etc/redhat-release ]; then 	
    yum install -y git
    yum install -y zip unzip
    yum install -y python-setuptools
    yum install -y python-pip
fi
if [ -d /etc/apt/ ]; then
    apt-get install -y git
    apt-get install -y zip unzip
    apt-get install -y python-setuptools
    apt-get install -y python-pip
fi
wget https://releases.hashicorp.com/terraform/0.10.8/terraform_0.10.8_linux_amd64.zip
unzip terraform_0.10.8_linux_amd64.zip
mv terraform /usr/local/bin/
pip install jinja2
pip install gitpython
terraform init
