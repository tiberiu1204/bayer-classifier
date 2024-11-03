import numpy as np
from pathlib import Path
import os
import threading
import subprocess
from typing import List
import json
from collections import Counter
import copy

FILES = ["antena3.json", "wowbiz.json", "pressone.json"]
PROJECT_ROOT = f"{os.getcwd()}/.."
CRAWLER_DIR = f"{PROJECT_ROOT}/scraper"
CLASSIFIER_DIR = os.getcwd()


class Classifier:
    def __init__(self):
        self._check_if_files_exist(FILES)
        self.data = self._load_json(FILES)
        self._analize_freq()
    """
    Check if required json files containing necessary data are present in
    current directory.

    If not present, the function will execute a subprocess for each missing
    file that will scrape the data.

    Parameters:
        files (string list): List of files to check

    Returns: None

    """

    def _check_if_files_exist(self, files: List[str]) -> None:
        files_not_present = [
            file for file in files if not Path(file).is_file()]

        threads = []
        for file in files_not_present:
            command = f"scrapy crawl {file.split(
                '.')[0]} -O {CLASSIFIER_DIR}/{file} -s LOG_LEVEL=CRITICAL"

            os.chdir(CRAWLER_DIR)

            thread = threading.Thread(
                target=lambda: subprocess.run(command, shell=True))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    def _load_json(self, files: List[str]) -> dict:
        data = {}
        for file in files:
            with open(file, 'r') as f:
                data[file] = json.load(f)
        return data

    def _analize_freq(self) -> dict:
        self.freq_dict_per_article = copy.deepcopy(self.data)
        self.freq_dict = {}
        for file_name, data_point in self.freq_dict_per_article.items():
            dicts = []
            for article in data_point:
                article["text"] = Counter(article["text"])
                dicts.append(article["text"])
            self.freq_dict[file_name] = sum(dicts, Counter())


classifier = Classifier()
