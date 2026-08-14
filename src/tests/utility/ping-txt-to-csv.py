import sys
import os
import argparse
import csv
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))



# Regex pattern to capture icmp_seq and time from typical ping output
# Matches both Windows (time=23ms) and Unix/Linux/macOS (icmp_seq=1 time=23.4 ms)
pattern = re.compile(r"icmp_seq=(\d+).*?time=([\d\.]+)")


def parse_ping_to_csv(txt_file, csv_file):
    parsed_data = []

    with open(txt_file, "r") as file:
        for line in file:
            match = pattern.search(line)
            if match:
                icmp_seq = match.group(1)
                time_ms = match.group(2)
                parsed_data.append([icmp_seq, time_ms])

    # Write extracted data to CSV
    with open(csv_file, "w", newline="") as file:
        writer = csv.writer(file)
        # Write Header
        writer.writerow(["icmp_seq", "time"])
        # Write Rows
        writer.writerows(parsed_data)

    print(
        f"Successfully converted {len(parsed_data)} ping entries to {csv_file}"
    )

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        metavar="TXT_FILE",
        help="Path to input text file."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="CSV_FILE",
        help="Output file name."
    )
    args = parser.parse_args()

    #output directoy paths
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    output_dir = os.path.join(root, "latency-reports")
    if args.output:
        output_csv_file = os.path.join(output_dir, args.output)
    else:
        output_csv_file = os.path.join(output_dir, "ping_report.csv")

    if args.input:
        parse_ping_to_csv(args.input, output_csv_file)
    else:
        print("[ERROR] No input file provided.")
        parser.print_help()