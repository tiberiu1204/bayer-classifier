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
TABLOID = ["wowbiz.json", "antena3.json"]
PROJECT_ROOT = f"{os.getcwd()}/.."
CRAWLER_DIR = f"{PROJECT_ROOT}/scraper"
CLASSIFIER_DIR = os.getcwd()

def transform_to_classifier_fmt(article):
    return list(map(str.lower, article.split()))

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

        def calculate_multiplier(class_):
            class_features = Ps_of_features[class_]
            Ps_of_relevant_features = [value for feature, value in class_features.items() if feature in features]
            return np.prod(Ps_of_relevant_features) if Ps_of_relevant_features else 0

        # using ThreadPoolExecutor to parallelize the computation
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            multipliers = list(executor.map(calculate_multiplier, Ps_of_classes))

        multipliers = np.array(multipliers)
        result = Ps_of_classes_values * multipliers
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
        self.Ps_goodbad = {}
        total_art = 0
        for file_name, article_arr in self.word_sets.items():
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
                ((key, percentage) for key, value in self.freq[category].items()
                 if (percentage := round(float(value) / len(article_arr), 2))),
                key=lambda item: item[1], reverse=True
            ))

    total_art = 0
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
                self.total_art += 1
        self.Ps_cat = copy.deepcopy(art_per_cat)
        for category in self.freq_categories:
            self.Ps_cat[category] /= self.total_art
            self.freq_categories[category] = dict(sorted(
                ((key, percentage) for key, value in self.freq_categories[category].items() if (
                    percentage := round(float(value) / art_per_cat[category], 2))),
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

article = transform_to_classifier_fmt('Cei cinci minori acuzați că au violat o adolescentă de 15 ani - cu toții protagoniști ai unui scandal deja celebru din Constanța - au fost arestați preventiv de magistrații constănțeni. Odată cu ei, după gratii a ajuns și un tânăr, care s-a recomandat ca fiind vărul unuia dintre suspecți, pentru șantaj. Procurorii Parchetului de pe lângă Judecătoria Constanța, în atenția cărora se află dosarul, au menționat, în referatul de arestare preventivă următoarele, cu privire la derularea evenimentelor: "În noaptea de 14 spre 15 decembrie 2013, profitând de starea tinerei Roxana B. și de imposibilitatea acesteia de a-și exprima consimțământul, cei cinci inculpați minori au condus-o pe partea vătămată la locuința unuia dintre ei, lipsind-o de libertate". Aici, spun anchetatorii, inculpații Dan Cristian I. și Severius Alexandru V. au întreținut raporturi sexuale cu partea vătămată, contrar voinței acesteia, fiind încurajați și susținuți fizic de inculpatul Cristian Floris G.; ulterior, în aceeași noapte, inculpații au condus-o pe partea vătămată la locuința sa, unde au intrat fără acord, context în care inculpatul Cristian Floris G. a întreținut raporturi sexuale cu minora, "fiind susținut moral și fizic de ceilalți patru inculpați", se arată în referatul de arestare preventivă întocmit de procurori. Cât privește acuzațiile ce le sunt aduse, procurorii au menționat: Cristian Floris G. și Severius Alexandru V. sunt acuzați de viol, complicitate la viol, lipsire de libertate în mod ilegal și violare de domiciliu; Dan Cristian I. este acuzat de viol (două acte), lipsire de libertate în mod ilegal și violare de domiciliu; Sever Tekin A. și Flavius Evelin Vasile Ș. sunt acuzați de complicitate la viol (câte două acte materiale), lipsire de libertate în mod ilegal și violare de domiciliu. Anchetatorii au mai precizat că, după comiterea faptelor, în perioada 15 - 22 decembrie, inculpatul Răzvan Cladiu S. (cel care s-a recomandat ca fiind vărul lui Severius Alexandru V.), prin intermediul unor postări pe o rețea de socializare i-a amenințat pe inculpații Dan Cristian I. și Cristian Floris G. cu acte de violență fizică și psihică, în cazul în care aceștia nu-și vor asuma exclusiv vinovăția faptelor, cu scopul de a-l exonera de răspundere pe cel despre care spunea că este vărul lui. Pentru acesta, este acuzat de două infracțiuni de șantaj. Vineri dimineață, cei șase suspecți au fost duși în fața instanței de judecată, magistrații dispunând arestarea lor, astfel: Cristian Floris G. pe o durată de 19 zile, Dan Cristian I., Severius Alexandru V., Sever Tekin A. și Flavius Evelin Vasile Ș., pentru 14 zile și patru ore, iar Răzvan Claudiu S., pentru 29 de zile. Menționăm că și la nivelul Inspectoratului Județean Școlar Constanța au fost luate măsuri în privința unora dintre elevii implicați în scandalul sexual. Astfel, doi dintre elevi au fost propuși spre mutarea disciplinară. "Facem precizarea că punerea în mișcare a acțiunii penale este o etapă a procesului penal reglementată de Codul de procedură penală, necesară în vederea propunerii unor măsuri preventive, activitate care nu poate, în nicio situație, să înfrângă principiul prezumției de nevinovăție", au subliniat anchetatorii din cadrul Parchetului de pe lângă Judecătoria Constanța. ')
print(classifier.total_art)
classifier.naive_bayes_infer(classifier.Ps_cat, classifier.freq_categories, article)
classifier.naive_bayes_infer(classifier.Ps_goodbad, classifier.freq, article)