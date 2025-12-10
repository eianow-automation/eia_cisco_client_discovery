#!/usr/bin/python -tt
# Project: eia_cisco_client_discovery
# Filename: seed_devlist
# claudia
# PyCharm

from __future__ import absolute_import, division, print_function

__author__ = "Claudia de Luna (claudia@eianow.com)"
__version__ = ": 1.0 $"
__date__ = "2/20/21"
__copyright__ = "Copyright (c) 2018 Claudia"
__license__ = "Python"

import argparse
import utils

# import add_2env
import os
import re
import dotenv
import datetime

# from rich.console import Console
# from rich.table import Table


def get_list_of_nei(cdp_list, root_dev, level=0, debug=False):

    devices_dict = dict()
    filter_regex_list = r".+(WS-)?C\d{4}"

    # For every neighbor found weed out connections to self and connections to upstream root device
    for line in cdp_list:
        print(line)
        print(line.keys())

        tmpd = dict()

        if re.search(filter_regex_list, line["platform"]):

            tmpd.update(
                {
                    "fqdn": line["neighbor_name"],
                    "mgmt_ip": line["mgmt_address"],
                    "platform": line["platform"],
                }
            )

            if line["neighbor_name"] not in devices_dict.keys():
                devices_dict.update({line["neighbor_name"]: tmpd})

    return devices_dict


def main():

    datestamp = datetime.date.today()
    print(f"\n========== Date is {datestamp} =========")

    # Load Credentials from environment variables
    dotenv.load_dotenv(verbose=False)

    # usr_env = add_2env.check_env("NET_USR")
    # pwd_env = add_2env.check_env("NET_PWD")
    # print(add_2env.check_env("INET_USR"))

    # SAVING OUTPUT
    # utils.sub_dir(arguments.output_subdir)

    if arguments.mfa:
        # User is using MFA
        usr = os.environ["INET_USR"]
        pwd = os.environ["INET_PWD"]
        sec = os.environ["INET_PWD"]
        mfa_code = input("Enter your VIP Access Security Code: ")
        mfa = f"{pwd}{mfa_code.strip()}"
        sec = sec
    elif arguments.credentials:
        # uname, passwd, enable = utils.get_creds()
        usr = uname
        mfa = passwd
        sec = enable
    else:
        # User has account without MFA
        usr = os.environ["NET_USR"]
        pwd = os.environ["NET_PWD"]
        sec = os.environ["NET_PWD"]
        mfa = pwd
        sec = pwd

    # if not usr_env["VALID"] and not pwd_env["VALID"]:
    #     add_2env.set_env()
    #     # Call the set_env function with a description indicating we are setting a password and set the
    #     # sensitive option to true so that the password can be typed in securely without echo to the screen
    #     add_2env.set_env(desc="Password", sensitive=True)

    # Create login object for netmiko
    seed_device = "10.1.10.66"
    dev_obj = {}
    dev_obj.update({"ip": seed_device.strip()})
    dev_obj.update({"username": "cisco"})
    dev_obj.update({"password": "cisco"})
    dev_obj.update({"secret": "cisco"})
    dev_obj.update({"port": arguments.port})
    dev_obj.update({"device_type": "cisco_ios"})

    root_dict = {}
    print(f"\n========== GET NEIGHBORS FROM SEED DEVICE {seed_device} ==========")

    resp_hostname = utils.conn_and_get_output_parsed(
        dev_obj, "show run | inc hostname "
    )

    if resp_hostname:
        _ = resp_hostname.split(" ")
        hostname = _[1].strip()
        if "\n" in hostname:
            _ = hostname.split("\n")
            hostname = _[0].strip()
    else:
        hostname = seed_device.strip()
    print(f"Device hostname is {hostname}")

    resp = utils.conn_and_get_output_parsed(dev_obj, "show inventory")

    if resp:
        if resp[0]["pid"]:
            platform = resp[0]["pid"]
        else:
            platform = resp[0]["descr"]

        root_dict.update(
            {"fqdn": seed_device, "mgmt_ip": seed_device, "platform": platform}
        )

        resp = utils.conn_and_get_output_parsed(dev_obj, "show cdp neighbors detail")
        if type(resp) == str and "not enabled" in resp:
            print(f"CDP is not enabled on device. Aborting process.")
            exit()

        cdp_dict = get_list_of_nei(resp, seed_device, level=0, debug=False)

        # print(json.dumps(cdp_dict, indent=4))

        cdp_dict.update({seed_device: root_dict})

        # The keys build the json dev list used by the other scripts in this repo
        list_of_devices = list(cdp_dict.keys())

        json_dir = arguments.output_subdir
        json_fn = f"{hostname.strip()}_auto_devlist.json"
        json_fp = os.path.join(os.getcwd(), json_dir, json_fn)

        # print(f"Saving {hostname} output to: {json_fp}")

        # Save a list of devices
        # utils.save_json(json_fp, list_of_devices, debug=False)

        # Save the JSON data
        # json_dict = os.path.join(os.getcwd(), json_dir, f"{hostname}_auto_devdict.json")
        # utils.save_json(json_dict, cdp_dict, debug=False)

        text_fn = f"{hostname}_devlist.txt"
        text_fp = os.path.join(os.getcwd(), json_dir, text_fn)
        # with open(text_fp, 'w') as txt_file:
        #     for line in list_of_devices:
        #         print(f"- {line}")
        #         txt_file.write(f"{line.strip()}\n")

        # table = Table(title=f"\n\nL3 Device {arguments.seed_device} CDP Switch Neighbor Summary Table")

        # table.add_column("Device", justify="right", style="cyan", no_wrap=True)
        # table.add_column("FQDN", style="green")
        # table.add_column("MGMT IP", justify="right", style="blue")
        # table.add_column("Platform", justify="right", style="yellow")

        # cdp_count = 0
        # for k,v in cdp_dict.items():
        #     table.add_row(k, v['fqdn'], v['mgmt_ip'], v['platform'])
        #     cdp_count += 1

        # console = Console()
        # console.print(table)
        # console.print(f"Total: {cdp_count}")

        # print(f"\nDevice Text file saved at {text_fp}\n")
        # print(f"\nDevice JSON List saved at {json_fp}\n")
        # print(f"\nDevice JSON Dictionary file saved at {json_dict}\n\n")

    else:
        print(f"ERROR!  No response from device! Aborting Execution.")


# Standard call to the main() function.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script Description",
        epilog="Usage: ' python seed_devlist.py layer3_device.example.com' ",
    )

    # parser.add_argument(
    #     "seed_device",
    #     help="Enter FQDN or IP of Seed or Root device to start CDP based device discovery",
    # )

    parser.add_argument(
        "-t",
        "--device_type",
        help="Device Types include cisco_nxos, cisco_asa, cisco_wlc Default: cisco_ios",
        action="store",
        default="cisco_ios",
    )
    parser.add_argument(
        "-p",
        "--port",
        help="Port for ssh connection. Default: 22",
        action="store",
        default="22",
    )
    parser.add_argument(
        "-o",
        "--output_subdir",
        help="Name of output subdirectory for show command files",
        action="store",
        default="local",
    )

    parser.add_argument(
        "-n",
        "--note",
        action="store",
        help="Short note to distinguish show commands. Ex. -pre or -post",
    )
    parser.add_argument(
        "-m",
        "--mfa",
        action="store_true",
        help="Multi Factor Authentication will prompt for VIP code",
        default=False,
    )
    parser.add_argument(
        "-c",
        "--credentials",
        action="store_true",
        help="Set Credentials via Command Line interactively",
        default="",
    )
    arguments = parser.parse_args()
    main()
