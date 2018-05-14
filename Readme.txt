# PNDA pico - rhel
1. Install git
	Ubuntu: apt-get install -y git
	RHEL: yum install -y git
2. Install wget 
	Ubuntu: apt-get install -y wget 
	RHEl: yum install -y wget
3. git clone https://github.com/TharanyaS/aws_pnda_pico_rhel.git
4. cd aws_pnda_pico_rhel/
5. Run install_packages.sh to install and initialize terraform and necessary packages
6. Copy your private_key_file to aws_pnda_pico_ubuntu directory
7. Provide your keypair name for ssh_key_name variable in variables.tf file
8. Run "terraform apply" command
9. Provide the values for access_key, secret_key, region and mirror_server_ip
Example:
var.access_key
  Enter a value: xxxx

var.secret_key
  Enter a value: xxxxxx

var.region
  Enter a value: us-east-1

var.mirror_server_ip
  Enter a value: 54.202.221.101
