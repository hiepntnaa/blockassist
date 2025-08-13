import json
import logging
import os
import signal
import sys
import threading
import time
from subprocess import Popen
from typing import Dict, Optional

import psutil
import readchar

from daemon import PROCESSES, cleanup_processes, start_log_watcher

TOTAL_TIME_PLAYED = 0
EPISODES_PLAYED = 0


def create_logs_dir(clear_existing=True):
    if os.path.exists("logs") and clear_existing:
        print("Clearing existing logs directory")
        cmd = "rm -rf logs"
        process = Popen(cmd, shell=True)
        ret = process.wait()
        if ret != 0:
            sys.exit(ret)

    print("Creating logs directory")
    cmd = "mkdir -p logs"
    process = Popen(cmd, shell=True)
    ret = process.wait()
    if ret != 0:
        sys.exit(ret)


def create_evaluate_dir():
    if not os.path.exists("data/base_checkpoint/evaluate"):
        print("Creating evaluate directory")
        cmd = "mkdir -p data/base_checkpoint/evaluate"
        process = Popen(cmd, shell=True)
        ret = process.wait()
        if ret != 0:
            sys.exit(ret)
    else:
        print("Evaluate directory already exists")


def setup_venv():
    logging.info("Running setup_venv")
    cmd = "./scripts/venv_setup.sh | tee logs/venv.log"
    process = Popen(cmd, shell=True)
    ret = process.wait()
    if ret != 0:
        sys.exit(ret)


def setup_gradle():
    logging.info("Running setup_gradle")
    cmd = "./scripts/gradle_setup.sh"
    process = Popen(cmd, shell=True)
    PROCESSES.append(process)
    ret = process.wait()
    if ret != 0:
        sys.exit(ret)


def setup_yarn():
    logging.info("Running setup_yarn")
    cmd = "./scripts/yarn_setup.sh"
    process = Popen(cmd, shell=True)
    PROCESSES.append(process)
    ret = process.wait()
    if ret != 0:
        sys.exit(ret)


def run_yarn():
    logging.info("Running run_yarn")
    cmd = "./scripts/yarn_run.sh"
    process = Popen(cmd, shell=True)
    PROCESSES.append(process)
    return process


def run_open():
    logging.info("Running run_open")
    cmd = "open http://localhost:3000 2> /dev/null"
    process = Popen(cmd, shell=True)
    PROCESSES.append(process)
    return process


def train_blockassist(env: Optional[Dict] = None):
    logging.info("Running train_blockassist")
    cmd = "./scripts/train_blockassist.sh"
    process = Popen(cmd, shell=True, env=env)
    PROCESSES.append(process)
    return process


def wait_for_login():
    logging.info("Running wait_for_login")
    # Extract environment variables from userData.json
    print("Waiting for modal userData.json to be created...")
    user_data_path = "modal-login/temp-data/userData.json"
    user_api_key_path = "modal-login/temp-data/userApiKey.json"
    while not os.path.exists(user_data_path):
        time.sleep(1)
    print("Found userData.json. Proceeding...")

    # Read and parse the JSON file
    while True:
        try:
            with open(user_data_path, "r") as f:
                user_data = json.load(f)

            with open(user_api_key_path, "r") as f:
                user_api_key = json.load(f)

            d = os.environ.copy()

            for k in user_data.keys():
                d["BA_ORG_ID"] = user_data[k]['orgId']
                d["BA_ADDRESS_EOA"] = user_data[k]['address']
                d["PYTHONWARNINGS"] = "ignore::DeprecationWarning"

            for k in user_api_key.keys():
                # Get the latest key
                d["BA_ADDRESS_ACCOUNT"] = user_api_key[k][-1]["accountAddress"]
                return d
        except Exception as e:
            print("Waiting...")
            time.sleep(1)   



def run():
    global TOTAL_TIME_PLAYED
    global EPISODES_PLAYED
    print("Creating directories...")
    create_logs_dir(clear_existing=True)
    create_evaluate_dir()

    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        filename="logs/run.log",
        level=logging.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logging.info("Running BlockAssist run.py script")
    print(
        """
██████╗ ██╗      ██████╗  ██████╗██╗  ██╗
██╔══██╗██║     ██╔═══██╗██╔════╝██║ ██╔╝
██████╔╝██║     ██║   ██║██║     █████╔╝
██╔══██╗██║     ██║   ██║██║     ██╔═██╗
██████╔╝███████╗╚██████╔╝╚██████╗██║  ██╗
╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝

 █████╗ ███████╗███████╗██╗███████╗████████╗
██╔══██╗██╔════╝██╔════╝██║██╔════╝╚══██╔══╝
███████║███████╗███████╗██║███████╗   ██║
██╔══██║╚════██║╚════██║██║╚════██║   ██║
██║  ██║███████║███████║██║███████║   ██║
╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚══════╝   ╚═╝

By Gensyn
        """
    )

    if os.environ.get("HF_TOKEN") is None:
        logging.info("HF_TOKEN not found, prompting")
        print(
            "Please enter your Hugging Face user access token and press ENTER. If you do not have a token, please refer to"
        )
        print()
        print("\n    https://huggingface.co/docs/hub/en/security-tokens")
        print()
        print("for instructions on how to obtain one.")

        while True:
            hf_token = input("Hugging Face token: ").strip()
            if hf_token:
                break

        os.environ["HF_TOKEN"] = hf_token
        print("HF_TOKEN set successfully")

    print("Setting up virtualenv...")
    setup_venv()

    print("Setting up Gradle...")
    setup_gradle()

    print("Compiling Yarn...")
    setup_yarn()

    print("\nLOGIN")
    print("========")
    if sys.platform == "darwin":
        print(
            "You will likely be asked to approve accessibility permissions. Please do so and, if necessary, restart the program."
        )
    proc_yarn = run_yarn()
    time.sleep(5)
    if not os.path.exists("modal-login/temp-data/userData.json"):
        print(
            "Running Gensyn Testnet login. If browser does not open automatically, please open a browser and go to http://localhost:3000 and click 'login' to continue."
        )
        print("Note, if it's your first time playing, also click 'log in')")
        run_open()

    env = wait_for_login()

    print("\nMODEL TRAINING")
    print("========")
    print("Your assistant is now training on the existing gameplay data.")
    print(
        "This may take a while, depending on your hardware. Please keep this window open until you see 'Training complete'."
    )
    print("Running training")
    proc_train = train_blockassist(env=env)
    proc_train.wait()

    print("Training complete")

    print("\nUPLOAD TO HUGGINGFACE AND SMART CONTRACT")
    print("========")
    # Monitor blockassist-train.log for HuggingFace upload confirmation and transaction hash
    print("Checking for upload confirmation and transaction hash...")
    train_log_path = "logs/blockassist-train.log"
    upload_confirmed = False
    transaction_hash = None
    hf_path = None
    hf_size = None

    # Wait up to 30 seconds for the logs to appear
    for attempt in range(30):
        time.sleep(1)

        try:
            # Check blockassist-train.log for both logs
            if os.path.exists(train_log_path):
                with open(train_log_path, "r") as f:
                    lines = f.readlines()
                    last_15_lines = lines[-15:] if len(lines) >= 15 else lines

                for line in last_15_lines:
                    line = line.strip()
                    if (
                        "Successfully uploaded model to HuggingFace:" in line
                        and not upload_confirmed
                    ):
                        line_elems = line.split(
                            "Successfully uploaded model to HuggingFace: "
                        )[1].split(" ")
                        hf_path = line_elems[0].strip()
                        hf_size = line_elems[3].strip() + " " + line_elems[4].strip()
                        print("SUCCESS: " + line)
                        upload_confirmed = True
                    elif "HF Upload API response:" in line and not transaction_hash:
                        print("BLOCKCHAIN: " + line)
                        transaction_hash = line

            # If we found both, we can stop monitoring
            if upload_confirmed and transaction_hash:
                print(
                    "Copy your HuggingFace model path (e.g. 'block-fielding/bellowing_pouncing_horse_1753796381') and check for it here:\nhttps://gensyn-testnet.explorer.alchemy.com/address/0xE2070109A0C1e8561274E59F024301a19581d45c?tab=logs"
                )
                break

        except Exception as e:
            print(f"Error reading log file: {e}")
            break

    # If we didn't find the logs after 30 seconds
    if not upload_confirmed and not transaction_hash:
        print(
            "WARNING: No upload confirmation or transaction hash found in blockassist-train.log"
        )
    elif not upload_confirmed:
        print("WARNING: No HuggingFace upload confirmation found in blockassist-train.log")
    elif not transaction_hash:
        print("WARNING: No transaction hash found in blockassist-train.log")

    print("\nSHUTTING DOWN")
    print("========")
    print("Stopping Yarn")
    proc_yarn.kill()

    print("SUCCESS! Your BlockAssist session has completed successfully!")
    print("")
    print("- Your gameplay was recorded and analyzed")
    print("- An AI model was trained on your building patterns")
    print("- The model was successfully uploaded to Hugging Face")
    print("- Your work helps train better AI assistants ")
    print("")
    print("Stats:")
    print("")
    print(f"- Episodes recorded: {EPISODES_PLAYED}")
    print(
        f"- Total gameplay time: {TOTAL_TIME_PLAYED // 60}m {TOTAL_TIME_PLAYED % 60}s"
    )
    print(f"- Model trained and uploaded: {hf_path}")
    print(f"- Model size: {hf_size}")
    print("")
    print("What to do next:")
    print("")
    print("")
    print(
        "- Run BlockAssist again to improve your performance (higher completion %, faster time)."
    )
    print(f"- Check your model on Hugging Face: https://huggingface.co/{hf_path}")
    print(
        "- Screenshot your stats, record your gameplay, and share with the community on X (https://x.com/gensynai) or Discord (https://discord.gg/gensyn)"
    )
    print("")
    print("Thank you for contributing to BlockAssist!")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_processes()
