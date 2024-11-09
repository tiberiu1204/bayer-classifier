import numpy as np
from fidx import fidx
import random
from pathlib import Path
import os
import threading
import subprocess
from typing import List
import json
from collections import Counter
import copy

FILES = ["antena3.json", "wowbiz.json", "pressone.json", "recorder.json"]
TABLOID = ["wowbiz.json", "antena3.json"]
PROJECT_ROOT = f"{os.getcwd()}/.."
CRAWLER_DIR = f"{PROJECT_ROOT}/scraper"
CLASSIFIER_DIR = os.getcwd()

def transform_to_classifier_fmt(article):
    return list(map(str.lower, article.split()))

class Classifier:
    word_sets_training = {}
    word_sets_testing = {}
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
        # self._compute_words_for_tabloid_classifier()
        # self._compute_words_for_category_classifier()

    """
    Check if required json files containing necessary data are present in
    current directory.

    If not present, the function will execute a subprocess for each missing
    file that will scrape the data.

    Parameters:
        files (string list): List of files to check

    Returns: None

    """

    #                                                          ↙ just list features into the function call
    def naive_bayes_infer(self, Ps_of_classes, Ps_of_features, features):  # < features is the article, split into words, as an array
        #                       ^ obvious,     ^ dict['class'] = dict2, where dict2['feature'] = P(feature | class)
        #                   dict['class'] = P(class)
        # given that denoinator is literally the exact same (P(features)) there's no sense in dividing anything

        Ps_of_classes_values = np.array(list(Ps_of_classes.values()))
        multipliers = []

        def normalize_to_probabilities(values):
            exp_values = np.exp(values - np.max(values))
            probabilities = exp_values / np.sum(exp_values)
            return probabilities

        def calculate_multiplier(class_):
            class_features = Ps_of_features[class_]
            Ps_of_relevant_features = [value for feature, value in class_features.items() if feature in features]
            return np.sum(np.log(Ps_of_relevant_features)) if Ps_of_relevant_features else 0

        # using ThreadPoolExecutor to parallelize the computation
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            multipliers = list(executor.map(calculate_multiplier, Ps_of_classes.keys()))

        multipliers = np.array(multipliers)
        result = normalize_to_probabilities(np.log(Ps_of_classes_values) + multipliers)
        result_dict = dict(zip(Ps_of_classes.keys(), result))
        print("The probability of belonging to each class are: ", result_dict)
        max_value = max(result_dict.values())
        max_classes = [class_ for class_, value in result_dict.items() if value == max_value]
        print("The article may be from: ", max_classes)
        return max_classes

    def _check_if_files_exist(self, files: List[str]) -> None:
        print("[INFO] Fetching jsons...")
        files_not_present = [
            file for file in files if not Path(file).is_file()]

        threads = []
        for file in files_not_present:
            command = f"scrapy crawl {file.split('.')[0]} -O {CLASSIFIER_DIR}/{file} -s LOG_LEVEL=CRITICAL"

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

    def _get_words_sets(self, test_percent=0.1) -> dict:
        print("[INFO] Building word sets...")
        for file_name, data_point in self.data.items():
            random.shuffle(data_point)
        self.word_sets_training = copy.deepcopy(self.data)
        self.word_sets_testing = copy.deepcopy(self.data)
        for file_name, data_point in self.word_sets_training.items():
            self.word_sets_training[file_name] = fidx(data_point)[:(1 - test_percent)]
            for article in data_point:
                article["text"] = set(map(str.lower, article["text"]))
        for file_name, data_point in self.word_sets_testing.items():
            self.word_sets_testing[file_name] = fidx(data_point)[(1 - test_percent):]
            for article in data_point:
                article["text"] = set(map(str.lower, article["text"]))

    def _calculate_frequencies_websites(self) -> dict:
        print("[INFO] Calculating frequencies for websites...")
        self.Ps_goodbad = {}
        total_art = 0
        for file_name, article_arr in self.word_sets_training.items():
            category = "tabloid" if file_name in TABLOID else "serious"
            self.freq[category] = Counter()
            self.Ps_goodbad.setdefault(category, 0)
            total_art += len(article_arr)
            for article in article_arr:
                self.freq[category] = self.freq[category] + \
                    Counter(article["text"])
                self.Ps_goodbad[category] += 1
        for category in self.freq:
            self.Ps_goodbad[category] /= total_art
            self.freq[category] = dict(sorted(
                ((key, probability) for key, value in self.freq[category].items()
                 if (probability := round(float(value) / len(article_arr), 2))),
                key=lambda item: item[1], reverse=True
            ))

    total_art = 0
    def _calculate_frequencies_categories(self) -> dict:
        print("[INFO] Calculating frequencies for categories...")
        art_per_cat = {}
        for file_name, article_arr in self.word_sets_training.items():
            for article in article_arr:
                text = article["text"]
                category = article["category"]
                if category not in self.freq_categories:
                    art_per_cat[category] = 1
                    self.freq_categories[category] = Counter()
                else:
                    art_per_cat[category] += 1
                    self.freq_categories[category] += Counter(text)
                self.total_art += 1
        self.Ps_cat = copy.deepcopy(art_per_cat)
        for category in self.freq_categories:
            self.Ps_cat[category] /= self.total_art
            self.freq_categories[category] = dict(sorted(
                ((key, probability) for key, value in self.freq_categories[category].items() if (
                    probability := round(float(value) / art_per_cat[category], 2))),
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

    def _test(self):
        passed_tests = 0
        total_tests = 0
        for file_name, data_point in self.word_sets_testing.items():
            if file_name in TABLOID:
                goodbad_class = "tabloid"
            else:
                goodbad_class = "serious"
            for article in data_point:
                total_tests += 1
                type_classes = self.naive_bayes_infer(classifier.Ps_cat, classifier.freq_categories, article["text"])
                goodbad_classes = self.naive_bayes_infer(classifier.Ps_goodbad, classifier.freq, article["text"])
                if article["category"] in type_classes:
                    passed_tests += 1
                print("Test nr. ", total_tests, " inferred class(es): ", type_classes, " true class: ", article["category"])

                if goodbad_class in goodbad_classes:
                    passed_tests += 1
                print("Test nr. ", total_tests, " inferred class(es): ", goodbad_classes, " true class: ", goodbad_class)
        print("Test complete, passed ", passed_tests/(2*total_tests) * 100, "% of tests.")




classifier = Classifier()
classifier._test()