import json
import requests
import subprocess
import time
import os
from datetime import datetime

CONFIG_FILE = "config.json"

with open(CONFIG_FILE) as f:
    config = json.load(f)

ALERT_FILE = config["alert_file"]
AI_API = config["ai_api"]

FRONTEND_VM = config["frontend_vm"]
FRONTEND_USER = config["frontend_user"]
PLAYBOOK = config["playbook_path"]

BENCHMARK_FILE = "benchmark_results.csv"

processed_ids = set()


def save_benchmark(
    alert_id,
    rule_id,
    decision,
    ai_time,
    total_time
):

    file_exists = os.path.exists(
        BENCHMARK_FILE
    )

    with open(
        BENCHMARK_FILE,
        "a"
    ) as f:

        if not file_exists:

            f.write(
                "alert_id,"
                "rule_id,"
                "decision,"
                "ai_time,"
                "total_time\n"
            )

        f.write(
            f"{alert_id},"
            f"{rule_id},"
            f"{decision},"
            f"{ai_time:.4f},"
            f"{total_time:.4f}\n"
        )


def execute_playbook(
    action,
    target
):

    print(
        f"[PLAYBOOK] {action} -> {target}"
    )

    cmd = [
        "ssh",
        f"{FRONTEND_USER}@{FRONTEND_VM}",
        f"{PLAYBOOK} {action} {target}"
    ]

    subprocess.run(
        cmd
    )


def score_alert(alert):

    response = requests.post(
        AI_API,
        json=alert,
        timeout=10
    )

    return response.json()


def process_alert(alert):

    start_time = datetime.now()

    alert_id = alert.get("id")

    if alert_id in processed_ids:
        return

    processed_ids.add(alert_id)

    rule_id = str(
        alert.get("rule", {}).get("id", "")
    )

    print(
        f"\n[SOAR] Processing Alert "
        f"{alert_id} Rule={rule_id}"
    )

    print(
        f"[BENCHMARK] Alert received "
        f"{start_time}"
    )

    try:

        ai_start = datetime.now()

        result = score_alert(alert)

        ai_end = datetime.now()

        ai_elapsed = (
            ai_end - ai_start
        ).total_seconds()

        print(
            f"[BENCHMARK] AI scoring "
            f"{ai_elapsed:.4f}s"
        )

        print(
            "[AI RESULT]",
            result
        )

    except Exception as e:

        print(
            f"[AI ERROR] {e}"
        )

        return

    decision = result.get(
        "decision",
        "Manual Review"
    )

    if decision != "High Confidence":

        total_elapsed = (
            datetime.now() - start_time
        ).total_seconds()

        print(
            "[SOAR] Manual Review"
        )

        save_benchmark(
            alert_id,
            rule_id,
            decision,
            ai_elapsed,
            total_elapsed
        )

        return

    #
    # DDoS Detection
    #
    if rule_id == "100004":

        srcip = (
            alert.get("data", {})
                 .get("srcip")
        )

        if not srcip:

            srcip = (
                alert.get("srcip", "")
            )

        if srcip:

            execute_playbook(
                "ddos_block",
                srcip
            )

    #
    # Malware
    #
    elif rule_id == "100010":

        execute_playbook(
            "malware_isolate",
            "host"
        )

    #
    # Login Abuse
    #
    elif rule_id in [
        "5503",
        "100020"
    ]:

        username = (
            alert.get("data", {})
                 .get("dstuser")
        )

        if not username:

            username = "unknown"

        execute_playbook(
            "lock_user",
            username
        )

    end_time = datetime.now()

    total_elapsed = (
        end_time - start_time
    ).total_seconds()

    print(
        f"[BENCHMARK] Total response "
        f"{total_elapsed:.4f}s"
    )

    save_benchmark(
        alert_id,
        rule_id,
        decision,
        ai_elapsed,
        total_elapsed
    )


def follow(file):

    file.seek(
        0,
        os.SEEK_END
    )

    while True:

        line = file.readline()

        if not line:

            time.sleep(1)

            continue

        yield line


def main():

    print(
        f"[SOAR] Monitoring "
        f"{ALERT_FILE}"
    )

    with open(
        ALERT_FILE,
        "r"
    ) as logfile:

        for line in follow(logfile):

            line = line.strip()

            if not line:
                continue

            try:

                alert = json.loads(
                    line
                )

            except Exception:
                continue

            rule_id = str(
                alert.get(
                    "rule",
                    {}
                ).get(
                    "id",
                    ""
                )
            )

            interesting_rules = [

                "100004",

                "100010",

                "100020",

                "5503"

            ]

            if rule_id not in interesting_rules:
                continue

            print(
                f"\n[SOAR] Alert "
                f"Detected Rule={rule_id}"
            )

            process_alert(
                alert
            )


if __name__ == "__main__":
    main()