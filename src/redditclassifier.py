import os
import json
import nltk
import random

import textparser

from hashedindex import HashedIndex
from url import Url
from utils import get_path_from_url, search_files, get_url_from_path

# Reddit Developer API Notes
# t1_	Comment
# t2_	Account
# t3_	Link
# t4_	Message
# t5_	Subreddit
# t6_	Award
# t8_	PromoCampaign


def load_data_source(index, data_path, subreddit, page_samples, process=lambda x: x):
    pages_dir = os.path.join(data_path, 'pages')
    subreddits_dir = os.path.join(data_path, 'subreddits')
    sr_path = os.path.join(subreddits_dir, subreddit)

    # Dictionary of all available instances
    data = {}

    # Add pages from subreddit JSON file
    for json_file in os.listdir(sr_path):
        with open(os.path.join(sr_path, json_file)) as fp:
            post_data = json.load(fp)

        for post in post_data['data']['children']:
            # Only interested in link posts (but they all should ok)
            if post['kind'] == 't3':
                data[post['data']['url']] = subreddit

    # Add random sample from pages directory
    remaining = set(search_files(pages_dir)) - set(data.keys())
    for page_path in random.sample(remaining, page_samples):
        url = get_url_from_path(pages_dir, page_path)
        data[url] = None   # Unlabelled data

    # Add all the data to the index
    for url, label in data.items():
        post_url = Url(url)

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
                        index.add_term_occurrence(post_processed_token, url)

    # Return list of data points
    return data
