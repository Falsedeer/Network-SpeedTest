import os
import sys
import json
import logging
import requests
import tkinter as tk
from typing import Any
from pathlib import Path
from datetime import datetime
from tkinter import messagebox


def test_networkspeed(multithread: bool = False) -> dict[str, Any]:
	""" Test the network download/upload speed. """
	import speedtest
	logger = logging.getLogger(__name__)

	try:
		test = speedtest.Speedtest()
		thread_count = os.cpu_count() if multithread else 1
		logger.info(f"Performing SpeedTest under {thread_count} threads.")
	
		# find the nearest server for most accurate result
		server = test.get_best_server()
		logger.info(f"Auto selected server: {server}")

		# test download / upload speed
		test.download(threads=thread_count)
		test.upload(threads=thread_count)

		# export result in dict
		test.results.share()
		report = test.results.dict()
		logger.info(f"SpeedTest report: {report}")
		return report

	except Exception as ex:
		logger.critical(f"Failed performing SpeedTest, Error: {ex}")
		return {}


def export_json(data: dict[str, Any], filepath: str) -> bool:
	""" Export the dictionary into JSON format and save on disk """
	logger = logging.getLogger(__name__)

	try:
		with open(filepath, "w") as file:
			json.dump(data, file, indent=4, sort_keys=True)

		return True

	except (OSError, TypeError, ValueError) as ex:
		logger.critical(f"Failed exporting dict as JSON, Error: {ex}")


def pop_messagebox(title: str, message: str) -> None:
	""" Create a pop up messagebox which is floating on the top """
	root = tk.Tk()
	root.withdraw()
	root.attributes("-topmost", True)
	messagebox.showinfo(title, message, parent=root)


def download_file(url: str, filepath: str) -> bool:
	""" Fetch the resource from internet and save on disk """
	logger = logging.getLogger(__name__)

	try:
		response = requests.get(url)
		with open(filepath, "wb") as file:
			file.write(response.content)

		return True

	except requests.exceptions.RequestException as ex:
		logger.critical("Failed Downloading file from {url}, Error: {ex}")
		return False

	except OSError as ex:
		logger.critical("Failed writing content to {filetpath}, Error: {ex}")
		return False


def init_logger(logfile: str) -> None:
	""" Initialize a global file logger with custom formatting """
	file_handler = logging.FileHandler(logfile, mode="w", encoding="utf-8")
	file_format = logging.Formatter(
		"{asctime} - {levelname} - {message} ({module})",
		style="{",
		datefmt="%Y-%m-%d %H:%M:%S"
	)
	file_handler.setFormatter(file_format)

	# register the handler in root logger
	logger = logging.getLogger()
	logger.setLevel(logging.INFO)
	logger.addHandler(file_handler)



if __name__ == "__main__":
	# redirect the stdout and stderr for speedtest in GUI mode
	if sys.stdout is None:
		sys.stdout = open(os.devnull, 'w')
	if sys.stderr is None:
		sys.stderr = open(os.devnull, 'w')

	try:
		# acknoledge user program is running
		pop_messagebox("SpeedTest", "Result will be saved to folder: `Report`")

		# create the report directory
		report_folder = Path("Report")
		report_folder.mkdir(exist_ok=True)
		timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

		# setup the file logger
		init_logger(f"{report_folder}/speed.log")
		logger = logging.getLogger(__name__)

		# perform network speedtest
		report = test_networkspeed(multithread=True)
		if not report:
			logger.critical("Test Failed, Aborting......")
			pop_messagebox("SpeedTest", "Test Failed !!")
			sys.exit(1)

		# export the result in JSON to report folder
		logger.info(f"Exporting report to: {report_folder/timestamp}.json")
		stat = export_json(report, f"{report_folder/timestamp}.json")
		if not stat:
			logger.error("Failed saving result to destination location.")

		# donwload the report image for the test report
		logger.info(f"Donwloading the image report to: {report_folder/timestamp}.png")
		stat = download_file(report['share'], f"{report_folder}/{timestamp}.png")
		if not stat:
			logger.error("Failed saving image to destination location.")

		# acknoledge user program execution completed
		pop_messagebox("SpeedTest", "Test Completed !!")
		logger.info("SpeedTest Completed.")
		sys.exit(0)

	except Exception as ex:
		logger.critical(f"Encountered unexpected error: {ex}")
		pop_messagebox("SpeedTest", "Test Failed !!")
		sys.exit(1)