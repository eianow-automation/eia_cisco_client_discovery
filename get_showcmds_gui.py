#!/usr/bin/python -tt
# Project: eia_cisco_client_discovery
# Filename: get_showcmds.py
# claudia
# PyCharm

from __future__ import absolute_import, division, print_function, annotations

__author__ = "Claudia de Luna (claudia@eianow.com)"
__version__ = ": 1.0 $"
__date__ = "4/20/20"
__copyright__ = "Copyright (c) 2018 Claudia"
__license__ = "Python"


import os
import re
import dotenv
import streamlit as st

import utils


def main() -> None:
    """
    Streamlit GUI for running get_showcmds-style discovery.

    This provides a browser-based interface that mirrors the main options of
    get_showcmds.py while leaving the original CLI script unchanged.

    Run with:

        uv run streamlit run get_showcmds_gui.py

    or (if streamlit is installed in the active environment):

        streamlit run get_showcmds_gui.py

    Render the Streamlit UI and execute show commands based on user input.
    """

    # Set page configuration, including favicon shown on the browser tab
    st.set_page_config(
        page_title="EIA Cisco Client Discovery GUI",
        page_icon="images/EIA_Favicon.png",
        layout="wide",
    )

    st.title("EIA Cisco Client Discovery GUI")
    st.write(
        "This is a Streamlit-based front end for running the same discovery "
        "workflow as get_showcmds.py."
    )

    # Sidebar branding
    st.sidebar.image(
        "images/EIALogoFINAL_medium_DarkBackgroundSolid.jpg",
        caption="EIA Network Automation",
        width=250,
    )
    st.sidebar.markdown("🏠 [eianow.com](https://eianow.com)")

    dotenv.load_dotenv(verbose=False)

    st.sidebar.header("Devices")
    single_device = st.sidebar.text_input("Single Device (IP or FQDN)", "")
    devices_text = st.sidebar.text_area(
        "Devices (one per line, optional)",
        "",
        help="Paste or type a list of devices; equivalent to the -f option.",
    )
    uploaded_file = st.sidebar.file_uploader(
        "Load devices from file (optional)",
        type=["txt"],
        help=(
            "Upload a text file with one IP or FQDN per line; "
            "this mirrors the --file_of_devs option."
        ),
    )

    st.sidebar.header("Connection")
    device_type = st.sidebar.selectbox(
        "Device Type",
        ["cisco_ios", "cisco_nxos", "cisco_wlc", "cisco_asa"],
        index=0,
    )
    port = st.sidebar.number_input("SSH Port", min_value=1, max_value=65535, value=22)
    output_subdir = st.sidebar.text_input("Output Subdirectory", "local")

    st.sidebar.header("Show Commands")
    show_cmd = st.sidebar.text_input(
        "Single Show Command (optional)",
        "",
        help=(
            "If empty, the default command list for the selected device_type "
            "from show_cmds.yml will be used."
        ),
    )
    note = st.sidebar.text_input(
        "Note (optional, e.g. -pre or -post)", "", help="Used in the output filename."
    )

    st.sidebar.header("Authentication")
    use_mfa = st.sidebar.checkbox("Use MFA (INET_USR / INET_PWD)", value=False)
    use_cli_creds = st.sidebar.checkbox(
        "Prompt for credentials (NET_USR / NET_PWD)", value=False
    )

    st.sidebar.markdown("---")
    st.sidebar.write("Environment-based defaults:")
    st.sidebar.code(
        f"NET_USR={os.environ.get('NET_USR', '')}\nNET_PWD=*** (hidden)",
        language="bash",
    )

    st.subheader("Run Discovery")
    st.write(
        "Fill in the options in the sidebar, then click **Run get_showcmds** "
        "to execute the show commands and save output files."
    )

    if st.button("Run get_showcmds"):
        combined_devices_text = devices_text or ""

        if uploaded_file is not None:
            file_content = uploaded_file.read().decode("utf-8", errors="ignore")
            if combined_devices_text:
                combined_devices_text += "\n" + file_content
            else:
                combined_devices_text = file_content

        devices = utils.build_device_list(single_device, combined_devices_text)

        if not devices:
            st.error("Please provide at least one device (single or list).")
            return

        total_devices = len(devices)
        progress_bar = st.progress(0, text="Starting device processing...")

        # Prepare credentials in a way that mirrors get_showcmds.py
        if use_mfa:
            usr = os.environ.get("INET_USR", "")
            pwd = os.environ.get("INET_PWD", "")
            sec = os.environ.get("INET_PWD", "")
            mfa_code = st.text_input(
                "Enter your MFA code (VIP / MS Auth / etc.)",
                "",
                type="password",
            )
            if not mfa_code:
                st.error("Please enter an MFA code.")
                return
            mfa = f"{pwd}{mfa_code.strip()}"
        elif use_cli_creds:
            st.info(
                "Enter credentials (these are not stored). "
                "Equivalent to using the -c / --credentials option."
            )
            usr = st.text_input("Username", os.environ.get("NET_USR", ""))
            pwd = st.text_input("Password", "", type="password")
            sec = st.text_input("Enable password", "", type="password")
            mfa = pwd
        else:
            usr = os.environ.get("NET_USR", "")
            pwd = os.environ.get("NET_PWD", "")
            sec = os.environ.get("NET_PWD", "")
            mfa = pwd

        if not usr or not mfa:
            st.error(
                "Username and password (or MFA-combined password) must be set, "
                "either via environment or the fields above."
            )
            return

        # Ensure output directory exists
        utils.sub_dir(output_subdir)

        # Load command dictionary once
        cmd_dict = utils.read_yaml("show_cmds.yml")

        results = []

        for index, dev in enumerate(devices, start=1):
            with st.expander(f"Device {dev}", expanded=False):
                devdict = {
                    "device_type": device_type,
                    "ip": dev,
                    "username": usr,
                    "password": mfa,
                    "secret": sec,
                    "port": int(port),
                }

                # Determine commands as in get_showcmds.py
                if device_type in ["cisco_ios", "cisco_nxos", "cisco_wlc"]:
                    if show_cmd:
                        cmds = [show_cmd]
                    elif re.search("ios", device_type):
                        cmds = cmd_dict["ios_show_commands"]
                    elif re.search("nxos", device_type):
                        cmds = cmd_dict["nxos_show_commands"]
                    elif re.search("wlc", device_type):
                        cmds = cmd_dict["wlc_show_commands"]
                    else:
                        cmds = cmd_dict["general_show_commands"]
                else:
                    cmds = cmd_dict.get("general_show_commands", [])

                st.write("Running commands:")
                for c in cmds:
                    st.code(c)

                # Attempt to connect and collect output
                try:
                    resp = utils.conn_and_get_output(devdict, cmds, debug=True)
                except Exception as e:  # defensive, in case utils raises
                    st.error(f"Error connecting to device {dev}: {e}")
                    results.append({"device": dev, "error": "Login/connection error"})
                    resp = ""

                if not resp:
                    # Treat empty response as a login/connection issue
                    st.warning("No output collected; possible login or connection issue.")
                    results.append({"device": dev, "error": "Login/connection issue"})
                else:
                    # Construct output filename similar to get_showcmds.py timestamped files
                    from datetime import datetime

                    now = datetime.now()
                    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

                    if note:
                        note_text = utils.replace_space(note)
                        basefn = f"{dev}_{timestamp}_{note_text}.txt"
                    else:
                        basefn = f"{dev}_{timestamp}.txt"

                    output_path = os.path.join(os.getcwd(), output_subdir, basefn)
                    utils.write_txt(output_path, resp)

                    st.success(f"Saved output to {output_path}")
                    st.text_area(
                        "Output preview",
                        resp,
                        height=200,
                        key=f"output_preview_{dev}",
                    )

                    results.append({"device": dev, "output_path": output_path})

            # Update progress after each device
            progress = int(index / total_devices * 100)
            progress_bar.progress(progress, text=f"Processed {index}/{total_devices} devices")

        if results:
            st.subheader("Summary")
            for r in results:
                if "error" in r:
                    st.write(f"{r['device']}: {r['error']}")
                else:
                    st.write(f"{r['device']}: {r['output_path']}")


if __name__ == "__main__":  # pragma: no cover
    main()
