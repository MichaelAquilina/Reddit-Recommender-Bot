import os
import json
import nltk
import random

import textparser

from utils import get_path_from_url, search_files

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
                directory, filename = get_path_from_url(pages_dir, post['data']['url'])
                data[os.path.join(directory, filename)] = subreddit

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

            for token in textparser.word_tokenize(text, remove_case=True):

                # Handle "or" case represented by "/"
                for split_token in token.split('/'):
                    post_processed_token = process(split_token)
                    if post_processed_token:
                        index.add_term_occurrence(post_processed_token, page_path)

    # Return list of data points
    return data
