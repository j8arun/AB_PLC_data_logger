import os
import datetime
import csv
from pycomm3 import LogixDriver
import time
import logging
from logging.handlers import TimedRotatingFileHandler

def get_plc_data(ip_address, tag_names):
    with LogixDriver(ip_address) as plc:
        return plc.read(tag_names)

def create_csv_file(folder, filename, data):
    csv_file_path = os.path.join(folder, filename)
    with open(csv_file_path, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        for row_data in data:
            csv_writer.writerow(row_data)

def read_config_file(filename):
    config = {}
    try:
        with open(filename, "r") as f:
            for line in f:
                key, value = line.strip().split(":")
                config[key.strip()] = value.strip()
    except FileNotFoundError:
        logging.error(f"Config file '{filename}' not found.")
        raise
    except Exception as e:
        logging.error(f"Error reading config file '{filename}': {e}")
        raise
    return config

def setup_logging(log_folder, log_file):
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_handler = TimedRotatingFileHandler(os.path.join(log_folder, log_file), when='midnight', interval=1, backupCount=30)
    log_handler.setFormatter(log_formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)
    root_logger.setLevel(logging.INFO)

def create_folders_if_not_exist():
    if not os.path.exists("logs"):
        os.makedirs("logs")

    if not os.path.exists("data"):
        os.makedirs("data")

def main():
    config_file = "config.txt"
    log_folder = "logs"
    log_file = "my_log_file.log"

    create_folders_if_not_exist()
    setup_logging(log_folder, log_file)

    try:
        config = read_config_file(config_file)

        plc_ip = config["IP"]
        tag_to_watch = config["TagToWatch"]
        tag_names = [tag.strip() for tag in config["Tags"].split(",")]
        sleep_time = int(config["sleepTime"])

        prev_tag_value = None

        while True:
            try:
                with LogixDriver(plc_ip) as plc:
                    current_tag_value = plc.read(tag_to_watch)

                if prev_tag_value is None or current_tag_value != prev_tag_value:
                    logging.info("Tag value changed. Fetching data and saving to CSV.")
                    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                    csv_folder = os.path.join("data", current_date)
                    if not os.path.exists(csv_folder):
                        os.makedirs(csv_folder)
                    csv_filename = os.path.join(csv_folder, f"data_{current_date}.csv")
                    data = get_plc_data(plc_ip, tag_names)
                    create_csv_file(csv_folder, f"data_{current_date}.csv", data)
                    prev_tag_value = current_tag_value

            except Exception as e:
                logging.error(f"PLC connection error: {e}")

            # Wait for the specified sleep interval before checking the tag again
            time.sleep(sleep_time)

    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
