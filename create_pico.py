import json
import subprocess
import time
import logging
import os
import argparse
from argparse import RawTextHelpFormatter
import shutil
from git import Repo
import jinja2
import yaml

LOGFILE = "deployment.log"
CONSOLE_LOGGER = None
FILE_LOGGER = None

def init_logging():
    global LOGFILE
    global CONSOLE_LOGGER
    global FILE_LOGGER
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    logging.basicConfig(filename=LOGFILE,
                        level=logging.INFO, filemode='w',
                        format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    FILE_LOGGER = logging.getLogger('filelogger')
    FILE_LOGGER.setLevel(logging.getLevelName('DEBUG'))
    CONSOLE_LOGGER = logging.getLogger('consolelogger')
    CONSOLE_LOGGER.addHandler(logging.StreamHandler())
    CONSOLE_LOGGER.setLevel(logging.getLevelName('DEBUG'))
init_logging()


def run_command(command):
    print command
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                CONSOLE_LOGGER.debug(output.strip())
        returncode = process.poll()
        return returncode
    except Exception as error:
        CONSOLE_LOGGER.error(str(error))


def clone_git_repo(repo_url, branch):
    """Clone pnda-cli git repository and checkout specified branch."""

    current_path = os.getcwd()
    pnda_path = os.path.join(current_path, 'pnda-cli')
    if os.path.exists(pnda_path):
        shutil.rmtree(pnda_path, ignore_errors=True)
    run_command("git clone -b {} {}" .format(branch, repo_url))
    return pnda_path

     
def create_production_json_file(flavor='pico'):
    """Create flavor.json file."""

    data = yaml.load(open("output.yaml"))
    output_dict = {}
    output_file = "%s.json" %flavor
    for key in data:
        node_name = key.split("_")[0]
        value = data[key]
        node_type = node_name
        if node_name == "public":
            continue
        if "mgr-1" in node_name and flavor == "pico":
            node_type = "hadoop-mgr"
        if isinstance(value, (str, unicode)):
            output_dict[node_name] = {}
            if node_name == "hadoop-edge":
                output_dict[node_name].update({"is_saltmaster":True, "is_console":True})
            if node_name == "bastion":
                output_dict[node_name].update({"is_bastion":True, "public_ip_address":data["public_ip"]})
            output_dict[node_name]["ip_address"] = value
            output_dict[node_name]["node_type"] = node_type
        else:
            for i in range(0, len(value)):
                output_dict[node_name+"-"+str(i)] = {}
                output_dict[node_name+"-"+str(i)]["ip_address"] = value[i]
                output_dict[node_name+"-"+str(i)]["node_type"] = node_type
    with open(output_file, "w") as json_data:
        json.dump(output_dict, json_data, sort_keys=True, indent=4)
    return output_file


def copy_key_and_json_file(key_name, json_file):
    """Copies private_key_file and json file to respective directories."""

    shutil.copy(json_file, './pnda-cli/existing-machines/')
    file_path = os.path.join('./pnda-cli/existing-machines', json_file)
    key_file = '%s.pem' % key_name
    shutil.copy(key_file, './pnda-cli')
    key_file = os.path.join('./pnda-cli', key_file)
    os.chmod(key_file, 0400)
    return os.path.abspath(file_path)


def create_env_file(input_data):
    """Update environment file for pnda-cli."""

    template_env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath='./'))
    template = template_env.get_template("pnda_env.j2")
    output = template.render(input_data)
    with open('./pnda-cli/pnda_env.yaml', 'w') as outfile:
        outfile.write(output)
    return None


def update_pnda_yaml(mirror_ip, access_key, secret_key, region, branch, os_user):
    """Update pnda_env.yaml file with user details."""

    config_data = json.load(open("input.json"))
    config_data.update({"mirror_ip": mirror_ip, "access_key": access_key, "secret_key": secret_key, "region": region, "branch": branch, "os_user": os_user})
    create_env_file(config_data)
    return None


def get_args():
    epilog = """
  - creates pico pnda cluster
    """

    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter,
                                     description='Creates PNDA pico cluster',
                                     epilog=epilog)
    parser.add_argument('command', help='Mode of operation',
                        choices=['create'])
    parser.add_argument('-i', '--mirror-ip',
                        help='Mirror server ip', required=True)
    parser.add_argument('-e', '--cluster-name', help='Cluster name', required=True)
    parser.add_argument('-b', '--branch', help='Branch of pnda-cli to checkout', required=True)
    parser.add_argument('-a', '--access-key', help='pnda variables to deploy PNDA', required=True)
    parser.add_argument('-r', '--region', help='pnda variables to deploy PNDA', required=True)
    parser.add_argument('-k', '--secret-key', help='pnda variables to deploy PNDA', required=True)
    parser.add_argument('-s', '--keypair', help='keypair name for \
                             ssh to mirror server', required=True)
    parser.add_argument('-u', '--user', help='Username to ssh into instances', required=True)
    parser.add_argument('-f', '--flavor', help='flavor of PNDA', required=True)
    args = parser.parse_args()
    return args


def deploy_pnda(args, pnda_path, json_path):
    try:
        path = os.path.join(pnda_path, 'cli')
        os.chdir(path)
        run_command('pip install -r requirements.txt')
        command = 'python pnda-cli.py create -e {} -s {} -m {} -f {} ' .format(args.cluster_name, args.keypair, json_path, args.flavor)
        FILE_LOGGER.info("Executing pnda-cli.py file")
        run_command(command)
        FILE_LOGGER.info("Please find socks proxy file in pnda-cli/cli folder...")
    except Exception as error:
        FILE_LOGGER(str(error))


def main():
    args = get_args()
    json_file_name = create_production_json_file()
    pnda_path = clone_git_repo("https://github.com/TharanyaS/pnda-cli.git", args.branch)
    json_path = copy_key_and_json_file(args.keypair, json_file_name)
    update_pnda_yaml(args.mirror_ip, args.access_key, args.secret_key, args.region, args.branch, args.user)
    deploy_pnda(args, pnda_path, json_path)


if __name__ == "__main__":
    try:
        main()
    except Exception as exception:
        FILE_LOGGER.error(exception)
        raise

