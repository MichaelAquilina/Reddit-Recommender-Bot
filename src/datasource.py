import os
import json
import nltk
import random

import textparser

from utils import search_files
from url import Url

# Reddit Developer API Notes
# t1_	Comment
# t2_	Account
# t3_	Link
# t4_	Message
# t5_	Subreddit
# t6_	Award
# t8_	PromoCampaign


def get_url_from_path(target_dir, abs_path):
    rel_path = os.path.relpath(abs_path, target_dir)

    if rel_path.endswith('%$%'):
        rel_path = rel_path[:-3]  # Remove special tag character

    return 'http://' + rel_path


def get_path_from_url(target_dir, url):
    if type(url) != Url:
        url = Url(url)

    directory = os.path.join(target_dir, url.hostname)

    # Create subdirs according to the url path
    url_path = url.path.strip('/')

    path_index = url_path.rfind('/')
    if path_index != -1:
        sub_path = url_path[:path_index].lstrip('/')
        directory = os.path.join(directory, sub_path)

        filename = url_path[path_index:].strip('/')
    else:
        filename = url_path

    # Root page directories are "index.html"
    if filename == '':
        filename = 'index.html'

    # Query can uniquely identify a file
    if url.query:
        filename += '?' + url.query

    # Append special character to prevent conflicts with directories
    filename += '%$%'

    return os.path.join(directory, filename)


def load_data_source(index, data_path, subreddit, page_samples, preprocess=lambda x: x):
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
                url_path = get_path_from_url(pages_dir, post['data']['url'])
                data[url_path] = subreddit

    # Add random sample from pages directory
    remaining = set(search_files(pages_dir)) - set(data.keys())
    for page_path in random.sample(remaining, page_samples):
        data[page_path] = None   # Unlabelled data

    # Add all the data to the index
    for page_path, label in data.items():

        if os.path.exists(page_path):
            with open(page_path, 'r') as html_file:
                html_text = html_file.read()

            # This currently provides good accuracy but does not
            # handle html tags very well
            text = nltk.clean_html(html_text)

            for token in textparser.word_tokenize(text):

                # Handle "or" case represented by "/"
                for split_token in token.split('/'):
                    if split_token:
                        index.add_term_occurrence(split_token, page_path)

    # Return list of data points
    return data
