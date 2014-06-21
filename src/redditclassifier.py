import os
import json
import nltk

import numpy as np

import textparser

from hashedindex import HashedIndex
from url import Url
from utils import get_path_from_url


# Try conform to sklearn's Estimator interface
class RedditClassifier(object):

    def __init__(self):
        self.index = HashedIndex()
        self.subreddits = None
        self._text_classification = None

    def _add_to_index(self, post, sr, pages_dir, process):
        post_url = Url(post['data']['url'])

        directory, filename = get_path_from_url(pages_dir, post_url)
        abs_path = os.path.join(directory, filename)
        rel_path = os.path.relpath(abs_path, pages_dir)

        if os.path.exists(abs_path):
            with open(abs_path, 'r') as html_file:
                html_text = html_file.read()

            # This currently provides good accuracy but does not
            # handle html tags very well
            text = nltk.clean_html(html_text)

            for token in textparser.word_tokenize(text, remove_case=True):

                # Handle "or" case represented by "/"
                for split_token in token.split('/'):
                    post_processed_token = process(split_token)
                    if post_processed_token:
                        self._text_classification[rel_path] = sr
                        self.index.add_term_occurrence(post_processed_token, rel_path)

    def load_data(self, data_path, subreddits=None, process=lambda x: x):
        pages_dir = os.path.join(data_path, 'pages')
        subreddits_dir = os.path.join(data_path, 'subreddits')

        # Store the classification of each document added
        self._text_classification = {}

        if subreddits is None:
            subreddits = os.listdir(subreddits_dir)

        # Assign the subreddits trained on
        self.subreddits = subreddits

        # Parse JSON subreddit files
        for sr in subreddits:
            sr_path = os.path.join(subreddits_dir, sr)

            for json_file in os.listdir(sr_path):
                with open(os.path.join(sr_path, json_file)) as fp:
                    post_data = json.load(fp)

                for post in post_data['data']['children']:
                    if post['kind'] == 't3':  # Only interested in link posts
                        self._add_to_index(post, sr, pages_dir, process)

    def generate_data(self):
        # Generate feature matrix from data loaded in the inverted index
        feature_matrix = self.index.generate_feature_matrix(mode='tfidf')

        # Generate the label vector
        label_vector = np.zeros((len(self.index.documents())))
        for i, document in enumerate(self.index.documents()):
            label_vector[i] = self.subreddits.index(self._text_classification[document])

        return feature_matrix, label_vector
