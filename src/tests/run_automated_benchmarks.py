# =========================== Usage Options ===========================
#
#   Full automated benchmark suite: python3 run_automated_benchmarks.py
#   Standalone analysis of report: python3 run_automated_benchmarks.py --analyze latency_report_file.json
#
# =====================================================================


import sys
import argparse
import json
import time
import os
import numpy as np
import roslibpy
from PyQt6.QtCore import (
    QCoreApplication
)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the RosBridgeConnection class
from RosBridgeConnection import RosBridgeConnection

ROSBROKER_IP = "192.168.0.102"
ROSBROKER_PORT = 9090
NAMESPACE = "/a200_0867"
NUM_TRIALS = 5
STEP_VELOCITY = 0.3
COOLDOWN_SEC = 2.5
STREAM_DURATION_SEC = 10.0


def build_command_id(trial_id: str, command_index: int) -> str:
    return f"{trial_id}:{command_index}"


def decode_command_id(command_id: str):
    if ":" not in command_id:
        return command_id, None
    trial_id, command_index = command_id.rsplit(":", 1)
    try:
        return trial_id, int(command_index)
    except ValueError:
        return command_id, None


def compute_message_latencies(sent_by_message, recv_by_message):
    latencies = []
    for message_id, sent_stamp in sent_by_message.items():
        recv_stamp = recv_by_message.get(message_id)
        if recv_stamp is not None:
            latencies.append((recv_stamp - sent_stamp) * 1000.0)
    return latencies


def run_test_suite():
    app = QCoreApplication.instance() or QCoreApplication(sys.argv)

    print(f"Connecting to RosBridge server at {ROSBROKER_IP}:{ROSBROKER_PORT}...")
    ros_conn = RosBridgeConnection()
    ros_conn.connect_to_bridge(ROSBROKER_IP, ROSBROKER_PORT)
    app.processEvents()

    # if not ros_conn.is_connected():
    #     raise ConnectionError(
    #         f"[ERROR] Failed to establish RosBridge connection to {ROSBROKER_IP}:{ROSBROKER_PORT}"
    #     )

    print("[SUCCESS] Connected to RosBridge.")

    client = ros_conn.client
    rpi_sub = roslibpy.Topic(client, "pi_test_metrics", "std_msgs/msg/String")
    husky_sub = roslibpy.Topic(client, f"{NAMESPACE}/test_metrics", "std_msgs/msg/String")

    trial_data = {}

    def pi_callback(msg):
        data = json.loads(msg['data'])
        raw_trial_id = data.get("trial_id")
        if raw_trial_id is None:
            return
        trial_id, _ = decode_command_id(raw_trial_id)
        if trial_id in trial_data:
            trial_data[trial_id]["pi_recv_stamps"][raw_trial_id] = data["pi_recv_stamp"]
            trial_data[trial_id]["pi_recv_stamp"] = data["pi_recv_stamp"]
            print(f"  [<-] Received Pi timestamp for {raw_trial_id}")

    def husky_callback(msg):
        data = json.loads(msg['data'])
        raw_trial_id = data.get("trial_id")
        if raw_trial_id is None:
            return
        trial_id, _ = decode_command_id(raw_trial_id)
        if trial_id in trial_data:
            trial_data[trial_id]["husky_recv_stamps"][raw_trial_id] = data["husky_recv_stamp"]
            trial_data[trial_id]["wheel_motion_stamps"][raw_trial_id] = data["wheel_motion_stamp"]
            trial_data[trial_id]["actuation_delay_ms_by_message"][raw_trial_id] = data["actuation_delay_ms"]
            trial_data[trial_id]["husky_recv_stamp"] = data["husky_recv_stamp"]
            trial_data[trial_id]["wheel_motion_stamp"] = data["wheel_motion_stamp"]
            trial_data[trial_id]["actuation_delay_ms"] = data["actuation_delay_ms"]
            print(f"  [<-] Received Husky Actuation delay for {raw_trial_id}: {data['actuation_delay_ms']} ms")

    rpi_sub.subscribe(pi_callback)
    husky_sub.subscribe(husky_callback)
    time.sleep(1.0)

    print(f"Starting Automated Latency Suite ({NUM_TRIALS} Trials)...")

    try:
        for seq in range(1, NUM_TRIALS + 1):
            if not ros_conn.is_connected():
                print(f"[!] Connection lost at trial {seq}. Aborting test suite.")
                break

            trial_id = f"trial_{seq}"

            # 1. Ensure Husky is fully stopped before starting trial
            ros_conn.publish_velocity(0.0, 0.0)
            time.sleep(COOLDOWN_SEC)

            # 2. Initialize a per-trial record and stamp the actual command send time,
            # not the wall-clock time at the start of the 10s loop.
            trial_data[trial_id] = {
                "trial_id": trial_id,
                "client_sent_stamp": None,
                "pi_recv_stamp": None,
                "husky_recv_stamp": None,
                "wheel_motion_stamp": None,
                "actuation_delay_ms": None,
                "client_sent_stamps": {},
                "pi_recv_stamps": {},
                "husky_recv_stamps": {},
                "wheel_motion_stamps": {},
                "actuation_delay_ms_by_message": {}
            }

            print(f"Trial {trial_id}/{NUM_TRIALS} dispatched; streaming for {STREAM_DURATION_SEC:.1f}s at 10 Hz...")

            # Stream commands at 10 Hz for a fixed duration to emulate a constant feed.
            trial_start = time.time()
            next_pub_time = trial_start
            end_time = trial_start + STREAM_DURATION_SEC
            command_index = 0

            while time.time() < end_time:
                app.processEvents()
                current_time = time.time()

                # 10 Hz publication loop with fixed cadence.
                if current_time >= next_pub_time:
                    message_id = build_command_id(trial_id, command_index)
                    publish_time = ros_conn.publish_velocity(STEP_VELOCITY, 0.0, frame_id=message_id)
                    trial_data[trial_id]["client_sent_stamps"][message_id] = publish_time
                    if trial_data[trial_id]["client_sent_stamp"] is None:
                        trial_data[trial_id]["client_sent_stamp"] = publish_time
                    command_index += 1
                    next_pub_time += 0.1

                time.sleep(0.01)

            if trial_data[trial_id]["actuation_delay_ms"] is None:
                print(f"[!] No actuation metrics received for {trial_id} during the 10s stream window.")

    finally:
        if ros_conn.is_connected():
            ros_conn.publish_velocity(0.0, 0.0, "base_link")
            rpi_sub.unsubscribe()
            husky_sub.unsubscribe()
            ros_conn.disconnect_from_bridge()

    raw_file = "latency_report_file.json"
    with open(raw_file, "w") as f:
        json.dump(trial_data, f, indent=4)

    analyze_and_save_results(raw_file)


def analyze_and_save_results(input_source, output_filepath="husky_latency_suite_report.json"):
    if isinstance(input_source, str):
        with open(input_source, "r") as f:
            raw = json.load(f)
            trial_data = raw.get("trials", raw)
    elif isinstance(input_source, dict):
        trial_data = input_source.get("trials", input_source)
    else:
        raise ValueError("input_source must be a dictionary or file path string.")

    actuation_delays = []
    client_to_pi_latencies = []
    pi_to_husky_latencies = []
    total_pipeline_latencies = []

    for metrics in trial_data.values():
        if metrics.get("actuation_delay_ms") is not None:
            actuation_delays.append(metrics["actuation_delay_ms"])

        sent_by_message = metrics.get("client_sent_stamps", {})
        recv_by_message = metrics.get("pi_recv_stamps", {})
        for message_id, sent_stamp in sent_by_message.items():
            recv_stamp = recv_by_message.get(message_id)
            if recv_stamp is not None:
                client_to_pi_latencies.append((recv_stamp - sent_stamp) * 1000.0)

        pi_by_message = metrics.get("pi_recv_stamps", {})
        husky_by_message = metrics.get("husky_recv_stamps", {})
        for message_id, pi_recv_stamp in pi_by_message.items():
            husky_recv_stamp = husky_by_message.get(message_id)
            if husky_recv_stamp is not None:
                pi_to_husky_latencies.append((husky_recv_stamp - pi_recv_stamp) * 1000.0)

        wheel_by_message = metrics.get("wheel_motion_stamps", {})
        for message_id, sent_stamp in sent_by_message.items():
            motion_stamp = wheel_by_message.get(message_id)
            if motion_stamp is not None:
                total_pipeline_latencies.append((motion_stamp - sent_stamp) * 1000.0)

        if not sent_by_message and metrics.get("pi_recv_stamp") and metrics.get("client_sent_stamp"):
            client_to_pi_latencies.append((metrics["pi_recv_stamp"] - metrics["client_sent_stamp"]) * 1000.0)

        if not pi_by_message and metrics.get("husky_recv_stamp") and metrics.get("pi_recv_stamp"):
            pi_to_husky_latencies.append((metrics["husky_recv_stamp"] - metrics["pi_recv_stamp"]) * 1000.0)

        if not sent_by_message and metrics.get("wheel_motion_stamp") and metrics.get("client_sent_stamp"):
            total_pipeline_latencies.append((metrics["wheel_motion_stamp"] - metrics["client_sent_stamp"]) * 1000.0)

    summary = {
        "total_trials": len(trial_data),
        "valid_trials": len(actuation_delays),
        "actuation_delay_ms": compute_stats(actuation_delays),
        "client_to_pi_ms": compute_stats(client_to_pi_latencies),
        "pi_to_husky_ms": compute_stats(pi_to_husky_latencies),
        "total_command_to_motion_ms": compute_stats(total_pipeline_latencies)
    }

    report = {"summary": summary, "trials": trial_data}

    with open(output_filepath, "w") as f:
        json.dump(report, f, indent=4)

    print("\n================== BENCHMARK SUMMARY ==================")
    print(f"Total Trials Evaluated:                 {summary['total_trials']}")
    print(f"Valid Actuation Trials:                 {summary['valid_trials']}")
    print(f"Actuation Delay (Husky Recv -> Motion): {summary['actuation_delay_ms']['mean']} ms (±{summary['actuation_delay_ms']['std']} ms)")
    print(f"Client -> Pi Latency:                   {summary['client_to_pi_ms']['mean']} ms")
    print(f"Pi -> Husky PC Latency:                 {summary['pi_to_husky_ms']['mean']} ms")
    print(f"Total Command -> Motion Pipeline:       {summary['total_command_to_motion_ms']['mean']} ms")
    print(f"Summary Report saved to:                {output_filepath}")
    print("=======================================================")


def compute_stats(arr):
    if not arr:
        return {"mean": 0, "std": 0, "min": 0, "max": 0, "p95": 0}
    np_arr = np.array(arr)
    return {
        "mean": round(float(np.mean(np_arr)), 2),
        "std": round(float(np.std(np_arr)), 2),
        "min": round(float(np.min(np_arr)), 2),
        "max": round(float(np.max(np_arr)), 2),
        "p95": round(float(np.percentile(np_arr, 95)), 2)
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="RosBridge Latency Suite & Analysis Tool")
    parser.add_argument(
        "--analyze",
        type=str,
        metavar="JSON_FILE",
        help="Run analysis directly on an existing JSON report file (e.g., latency_report_file.json)"
    )
    args = parser.parse_args()

    if args.analyze:
        analyze_and_save_results(args.analyze)
    else:
        run_test_suite()