import numpy as np
from pathlib import Path
import os
import threading
import subprocess
from typing import List
import json
from collections import Counter
import copy

FILES = ["antena3.json", "wowbiz.json", "pressone.json", "recorder.json"]
SERIOUS = ["pressone.json"]
TABLOID = ["wowbiz"]
PROJECT_ROOT = f"{os.getcwd()}/.."
CRAWLER_DIR = f"{PROJECT_ROOT}/scraper"
CLASSIFIER_DIR = os.getcwd()


class Classifier:
    word_sets = {}
    word_sets_union = {}
    freq = {}

    def __init__(self):
        self._check_if_files_exist(FILES)
        self.data = self._load_json(FILES)
        self._get_words_sets()
        self._calculate_frequencies()
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
        print("[INFO] Fetching jsons...")
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
        os.chdir(CLASSIFIER_DIR)
        print("[INFO] Loading jsons...")
        data = {}
        for file in files:
            with open(file, 'r') as f:
                data[file] = json.load(f)
        return data

    def _get_words_sets(self) -> dict:
        print("[INFO] Building word sets...")
        self.word_sets = copy.deepcopy(self.data)
        self.word_sets_union = {}
        for file_name, data_point in self.word_sets.items():
            sets = []
            for article in data_point:
                article["text"] = set(article["text"])
                sets.append(article["text"])
            self.word_sets_union[file_name] = set.union(*sets)

    def _calculate_frequencies(self) -> dict:
        print("[INFO] Calculating frequencies...")
        for file_name, article_arr in self.word_sets.items():
            self.freq[file_name] = Counter()
            for article in article_arr:
                self.freq[file_name] = self.freq[file_name] + \
                    Counter(article["text"])
            self.freq[file_name] = dict(sorted(
                ((key, percentage) for key, value in self.freq[file_name].items()
                 if (percentage := round(float(value) / len(article_arr) * 100, 2))),
                key=lambda item: item[1], reverse=True
            ))


classifier = Classifier()
