#!/usr/bin/python -tt
# Project: eia_cisco_client_discovery
# Filename: utils
# claudia
# PyCharm

from __future__ import absolute_import, division, print_function

__author__ = "Claudia de Luna (claudia@eianow.com)"
__version__ = ": 1.0 $"
__date__ = "9/27/20"
__copyright__ = "Copyright (c) 2018 Claudia"
__license__ = "Python"

import argparse
import yaml
import netmiko
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
import json
import os
import re
import dotenv
import getpass
import add_2env


def replace_space(text, debug=False):
    """
    Replace whitespace in a string with underscores and optionally print the change when debug is True.
    """
    newtext = re.sub(r"\s+", "_", text)
    if debug:
        print(f"Original Text: {text}\nReturning Text: {newtext.strip()}")
    return newtext.strip()


def load_env_from_dotenv_file(path):
    """
    Load key/value pairs from a .env file into environment variables, exiting if the file is missing.
    """
    # Load the key/value pairs in the .env file as environment variables
    if os.path.isfile(path):
        dotenv.load_dotenv(path)
    else:
        print(f"ERROR! File {path} NOT FOUND! Aborting program execution...")
        exit()


def read_yaml(filename):
    """
    Read a YAML file and return the loaded Python object.
    """
    with open(filename) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    return data


def read_json(filename, debug=False):
    """
    Read a JSON file and return the parsed data, optionally printing debugging information.
    """
    with open(filename) as f:
        data = json.load(f)
    if debug:
        print(f"\n...in the read_json function in utils.py")
        print(data)
        print(f"returning data of type {type(data)} with {len(data)} elements\n")
    return data


def save_json(filename, data, debug=False):
    """
    Save a Python object as pretty-printed JSON to the given filename, with optional debug output.
    """
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    if debug:
        print(f"\n...in the read_json function in utils.py")
        print(f"saved data to {filename}")


def write_txt(filename, data):
    """
    Write raw text data to the specified file and return the file handle.
    """
    with open(filename, "w") as f:
        f.write(data)
    return f


def sub_dir(output_subdir, debug=False):
    """
    Create the output_subdir directory if it does not exist, optionally logging when it already exists.
    """
    # Create target Directory if does not exist
    if not os.path.exists(output_subdir):
        os.mkdir(output_subdir)
        print("Directory ", output_subdir, " Created ")
    else:
        if debug:
            print("Directory ", output_subdir, " Already Exists")


def conn_and_get_output(dev_dict, cmd_list, debug=False):
    """
    Connect to a network device with Netmiko and run a list of show commands, returning the concatenated output.
    """

    response = ""
    try:
        net_connect = netmiko.ConnectHandler(**dev_dict)
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        print(f"Cannot connect to device {dev_dict['ip']}.")
        print(e)

    for cmd in cmd_list:
        if debug:
            print(f"--- Show Command: {cmd}")
        try:
            output = net_connect.send_command(cmd.strip())
            response += f"\n!--- {cmd} \n{output}"
        except Exception as e:
            print(f"Cannot execute command {cmd} on device {dev_dict['ip']}.")
            # continue

    return response


def load_environment(debug=False):
    """
    Ensure NET_USR and NET_PWD environment variables are set, prompting to create them if missing.
    """
    # Load Credentials from environment variables
    dotenv.load_dotenv(verbose=True)

    usr_env = add_2env.check_env("NET_USR")
    pwd_env = add_2env.check_env("NET_PWD")

    if debug:
        print(usr_env)
        print(pwd_env)

    if not usr_env["VALID"] and not pwd_env["VALID"]:
        add_2env.set_env()
        # Call the set_env function with a description indicating we are setting a password and set the
        # sensitive option to true so that the password can be typed in securely without echo to the screen
        add_2env.set_env(desc="Password", sensitive=True)


def open_file(filename, mode="r", encoding="utf-8", debug=False):
    """

    General Utility to safely open a file.

    encoding="utf-8"

    :param filename:  file to open
    :param mode: mode in which to open file, defaults to read
    :return:  file handle

    """

    if debug:
        print(
            f"in open_file function in cat_config_utils module with filename {filename} and mode as {mode}"
        )

    file_handle = ""
    # Mode = r | w | a | r+
    try:
        file_handle = open(filename, mode, encoding=encoding, errors="ignore")

    except IOError:
        print("IOError" + str(IOError))
        print(
            f"open_file() function could not open file with mode {mode} in given path {path}"
            f"\nPlease make sure all result files are closed!"
        )

    return file_handle


def get_creds(debug=True):
    """
    Function to interactively set credentials
    """

    user = input("Username [%s]: " % getpass.getuser())

    if not user:
        user = getpass.getuser()

    print("Password and Enable Password will not be echoed to the screen or saved.")

    pwd = getpass.getpass("Password: ")

    enable = getpass.getpass("Enable: ")

    return user, pwd, enable


def create_devobj_from_json_list(dev):
    """
        dev = {
        'device_type': 'cisco_nxos',
        'ip' : 'sbx-nxos-mgmt.cisco.com',
        'username' : user,
        'password' : pwd,
        'secret' : sec,
        'port' : 8181
    }
    """
    dotenv.load_dotenv()
    dev_obj = {}
    # print(os.environ)
    usr = os.environ["NET_USR"]
    pwd = os.environ["NET_PWD"]

    core_dev = r"(ar|as|ds|cs){1}\d\d"
    dev_obj.update({"ip": dev.strip()})
    dev_obj.update({"username": usr})
    dev_obj.update({"password": pwd})
    dev_obj.update({"secret": pwd})
    dev_obj.update({"port": 22})
    if re.search(core_dev, dev, re.IGNORECASE):
        dev_obj.update({"device_type": "cisco_ios"})
    elif re.search(r"-srv\d\d", dev, re.IGNORECASE):
        dev_obj.update({"device_type": "cisco_nxos"})
    elif re.search(r"-sp\d\d", dev, re.IGNORECASE):
        dev_obj.update({"device_type": "silverpeak"})
    elif re.search(r"-wlc\d\d", dev, re.IGNORECASE):
        dev_obj.update({"device_type": "cisco_wlc"})
    elif re.search("10.1.10.109", dev, re.IGNORECASE):
        dev_obj.update({"device_type": "cisco_wlc"})
        dev_obj.update({"username": "adminro"})
        dev_obj.update({"password": "Readonly1"})
        dev_obj.update({"secret": "Readonly1"})
        # dev_obj.update({'username': 'admin'})
        # dev_obj.update({'password': 'A123m!'})
        # dev_obj.update({'secret': 'A123m!'})
    elif re.search("10.1.10.", dev, re.IGNORECASE) or re.search(
        "1.1.1.", dev, re.IGNORECASE
    ):
        dev_obj.update({"device_type": "cisco_ios"})
    elif re.search("10.", dev, re.IGNORECASE):
        dev_obj.update({"device_type": "cisco_ios"})
    else:
        dev_obj.update({"device_type": "unknown"})

    return dev_obj


def get_show_cmd_parsed(dev, shcmd, save_2json=False, level=0, debug=False):
    """
    Run a parsed show command on a device, optionally saving JSON output, with simple verbosity control via level.
    """

    if level == 0:
        print(f"\n\n==== Device {dev} getting command {shcmd}")
    elif level == 1:
        print(f"\n\t\t--- Device {dev} getting command {shcmd}")
    elif level == 2:
        print(f"\n\t\t\t- Device {dev} getting command {shcmd}")

    outdir = "local"

    devdict = create_cat_devobj_from_json_list(dev)

    if debug:
        print(f"devdict is {devdict}")

    # Default to Cisco IOS device type
    if devdict["device_type"] == "unknown":
        devdict.update({"device_type": "cisco_ios"})

    # if devdict['device_type'] in ['cisco_ios', 'cisco_nxos', 'cisco_wlc']:
    resp = conn_and_get_output_parsed(devdict, shcmd)
    # print(resp)
    if save_2json:
        output_dir = os.path.join(
            os.getcwd(), outdir, f"{dev}_{shcmd.replace(' ', '_')}.json"
        )
        print(f"Saving JSON to {output_dir}")
        with open(output_dir, "w") as f:
            json.dump(resp, f, indent=4)
    # else:
    #     print(f"\n\n\txxx Skip Device {dev} Type {devdict['device_type']}")

    return resp


def conn_and_get_output_parsed(dev_dict, cmd, debug=False):
    """
    Connect to a device, run a single show command using TextFSM parsing, and return the structured output.
    """

    os.environ["NET_TEXTFSM"] = "./ntc-templates/ntc_templates/templates"

    response = ""
    output = ""

    try:
        net_connect = netmiko.ConnectHandler(**dev_dict)
    except NetmikoTimeoutException as e:
        print(f"Cannot connect to device {dev_dict['ip']}. Connection Timed Out!")
        print(e)
    except NetmikoAuthenticationException as e:
        print(f"Cannot connect to device {dev_dict['ip']}. Authentication Exception!")
        print(e)

    if debug:
        print(f"--- Show Command: {cmd}")
    try:
        output = net_connect.send_command(cmd.strip(), use_textfsm=True)
    except Exception as e:
        print(f"Cannot execute command {cmd} on device {dev_dict['ip']}.")
        print(f"{e}\n")

    return output


def main():
    """
    Entry point for invoking utils.py directly; currently a placeholder.
    """
    pass


# Standard call to the main() function.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script Description", epilog="Usage: ' python utils' "
    )

    # parser.add_argument('all', help='Execute all exercises in week 4 assignment')
    parser.add_argument(
        "-j",
        "--json_file",
        help="Name of JSON file with list of devices",
        action="store",
        default="ios_test.json",
    )
    parser.add_argument(
        "-o",
        "--output_subdir",
        help="Name of output subdirectory for show command files",
        action="store",
        default="TEST",
    )
    arguments = parser.parse_args()
    main()
