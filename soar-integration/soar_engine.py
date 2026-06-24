import json
import requests
import subprocess

CONFIG_FILE = "config.json"

with open(CONFIG_FILE) as f:
    config = json.load(f)

FRONTEND_VM = config["frontend_vm"]
FRONTEND_USER = config["frontend_user"]
PLAYBOOK = config["playbook_path"]

def execute_playbook(action, target):
    cmd = [
        "ssh",
        f"{FRONTEND_USER}@{FRONTEND_VM}",
        f"{PLAYBOOK} {action} {target}"
    ]

    subprocess.run(cmd)

def process_alert(alert):

    response = requests.post(
        "http://localhost:5000/score",
        json=alert
    )

    result = response.json()

    print(result)

    decision = result["decision"]

    if decision != "High Confidence":
        print("Manual Review")
        return

    rule_id = str(alert.get("rule", {}).get("id", ""))

    if rule_id == "100001":
        execute_playbook(
            "ddos_block",
            alert.get("srcip", "")
        )

    elif rule_id == "100002":
        execute_playbook(
            "malware_isolate",
            "host"
        )

    elif rule_id == "100003":
        execute_playbook(
            "lock_user",
            alert.get("user", "")
        )

if __name__ == "__main__":

    with open("sample_alert.json") as f:
        alert = json.load(f)

    process_alert(alert)