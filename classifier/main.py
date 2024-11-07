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
TABLOID = ["wowbiz.json"]
PROJECT_ROOT = f"{os.getcwd()}/.."
CRAWLER_DIR = f"{PROJECT_ROOT}/scraper"
CLASSIFIER_DIR = os.getcwd()


class Classifier:
    word_sets = {}
    word_sets_union = {}
    freq = {}
    freq_categories = {}
    tabloid_words = []
    words_by_category = {}

    def __init__(self):
        self._check_if_files_exist(FILES)
        self.data = self._load_json(FILES)
        self._get_words_sets()
        self._calculate_frequencies_websites()
        self._calculate_frequencies_categories()
        self._compute_words_for_tabloid_classifier()
        self._compute_words_for_category_classifier()

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
                article["text"] = set(map(str.lower, article["text"]))
                sets.append(article["text"])
            self.word_sets_union[file_name] = set.union(*sets)

    def _calculate_frequencies_websites(self) -> dict:
        print("[INFO] Calculating frequencies for websites...")
        for file_name, article_arr in self.word_sets.items():
            category = "tabloid" if file_name in TABLOID else "serious"
            self.freq[category] = Counter()
            for article in article_arr:
                self.freq[category] = self.freq[category] + \
                    Counter(article["text"])
        for category in self.freq:
            self.freq[category] = dict(sorted(
                ((key, percentage) for key, value in self.freq[category].items()
                 if (percentage := round(float(value) / len(article_arr) * 100, 2))),
                key=lambda item: item[1], reverse=True
            ))

    def _calculate_frequencies_categories(self) -> dict:
        print("[INFO] Calculating frequencies for categories...")
        art_per_cat = {}
        for file_name, article_arr in self.word_sets.items():
            for article in article_arr:
                text = article["text"]
                category = article["category"]
                if category not in self.freq_categories:
                    art_per_cat[category] = 1
                    self.freq_categories[category] = Counter()
                else:
                    art_per_cat[category] += 1
                    self.freq_categories[category] += Counter(text)
        for category in self.freq_categories:
            self.freq_categories[category] = dict(sorted(
                ((key, percentage) for key, value in self.freq_categories[category].items() if (
                    percentage := round(float(value) / art_per_cat[category] * 100, 2))),
                key=lambda item: item[1], reverse=True))

    def _compute_words_for_tabloid_classifier(self, difference=10, min_percentage=2) -> list:
        print("[INFO] Finding words to consider for tabloid/serious classifier...")
        word_arr = np.empty(0)
        for tabloid in TABLOID:
            np.append(word_arr, self.freq["tabloid"])
        tabloid_freqs = np.array(list(self.freq["tabloid"].values()))
        serious_freqs = np.array([self.freq["serious"].get(
            word, -difference + min_percentage) for word in self.freq["tabloid"]])
        diff = tabloid_freqs - serious_freqs

        tabloid_words = np.array(list(self.freq["tabloid"].keys()))

        filtered_words = tabloid_words[diff > difference]

        self.tabloid_words = filtered_words

    def _compute_words_for_category_classifier(self, difference=20, min_percentage=5) -> dict:
        print("[INFO] Finding words to consider for category classifier...")
        for category, freq_dict in self.freq_categories.items():
            curr_cat_freqs = np.array(list(freq_dict.values()))
            curr_cat_words = np.array(list(freq_dict.keys()))
            for category2, freq_dict2 in self.freq_categories.items():
                if category == category2:
                    continue
                cat2_freqs = np.array(
                    [freq_dict2.get(word, -difference + min_percentage) for word in curr_cat_words])
                diff = curr_cat_freqs - cat2_freqs
                filtered_words = curr_cat_words[diff > difference]
                self.words_by_category[category] = {}
                self.words_by_category[category][category2] = [
                    str(x) for x in list(filtered_words)]
        print(self.words_by_category)


classifier = Classifier()
