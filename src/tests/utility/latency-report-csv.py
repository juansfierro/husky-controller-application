import json
import csv
import argparse
import os

def parse_json_to_csv(json_file, csv_file):
    with open(json_file, "r") as report:
        trial_data = json.load(report)

    # print(trial_data)

    trial_num = []
    client_sent_stamp = []
    pi_recv_stamp = []
    husky_recv_stamp = []
    wheel_motion_stamp = []
    actuation_delay_ms = []

    client_dict = dict()
    pi_recv_dict = dict()
    husky_recv_dict = dict()
    wheel_motion_dict = dict()
    actuation_delay_dict = dict()

    # print(trial_data.keys())
    
    # Extract the timestamps per message within each trial's cluster
    for trial_key in trial_data.keys():
        client_dict |= trial_data[trial_key]["client_sent_stamps"]
        pi_recv_dict |= trial_data[trial_key]["pi_recv_stamps"]
        husky_recv_dict |= trial_data[trial_key]["husky_recv_stamps"]
        wheel_motion_dict |= trial_data[trial_key]["wheel_motion_stamps"]
        actuation_delay_dict |= trial_data[trial_key]["actuation_delay_ms_by_message"]

    # print(client_dict.keys())

    for key in list(client_dict):
        trial_num.append(key)

        client_sent_stamp.append(client_dict[key])
        pi_recv_stamp.append(pi_recv_dict[key])
        try:
            husky_recv_stamp.append(husky_recv_dict[key])
        except KeyError:
            husky_recv_stamp.append("")
        try:    
            wheel_motion_stamp.append(wheel_motion_dict[key])
        except KeyError:
            wheel_motion_stamp.append("")
        try:
            actuation_delay_ms.append(actuation_delay_dict[key])
        except KeyError:
            actuation_delay_ms.append("")

    with open(csv_file, "w", newline="") as output:
        writer = csv.writer(output)

        writer.writerow(["trial", "client_stamp", "pi_stamp", "husky_stamp", "wheel_stamp", "actuation_delay (ms)"])

        for col in range(0, len(trial_num)):
            row = []

            row.append(trial_num[col])
            row.append(client_sent_stamp[col])
            row.append(pi_recv_stamp[col])
            row.append(husky_recv_stamp[col])
            row.append(wheel_motion_stamp[col])
            row.append(actuation_delay_ms[col])

            writer.writerow(row)

    print(
        f"Succesfully converted {len(trial_num)} trials to {csv_file}"
    )

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        metavar="JSON_FILE",
        help="Path to latency report json"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="CSV_FILE",
        help="Output file name"
    )
    args = parser.parse_args()

    #output directory paths
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    output_dir = os.path.join(root, "latency-reports")
    if args.output:
        output_csv_file = os.path.join(output_dir, args.output)
    else:
        if os.path.isfile(os.path.join(output_dir, "latency_report.csv")):
            file_num = 1
            while os.path.isfile(os.path.join(output_dir, f"latency_report ({file_num}).csv")):
                file_num += 1

            output_csv_file = os.path.join(output_dir, f"latency_report ({file_num}).csv")
        else:
            output_csv_file = os.path.join(output_dir, "latency_report.csv")

    if args.input:
        parse_json_to_csv(args.input, output_csv_file)
    else:
        print("\033[33m[ERROR] No input file provided\033[0m")
        parser.print_help()
            