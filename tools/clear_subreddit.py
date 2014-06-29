import os
import json

from url import Url
from utils import get_path_from_url

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='Clear subreddit data from a data store')
    parser.add_argument('subreddit', type=str)
    parser.add_argument('path', type=str)

    # TODO: Add option to clear all directories which are empty

    args = parser.parse_args()

    sr_json_dir = os.path.join(args.path, 'subreddits', args.subreddit)
    pages_dir = os.path.join(args.path, 'pages')

    for json_file in os.listdir(sr_json_dir):
        abs_json_path = os.path.join(sr_json_dir, json_file)
        with open(abs_json_path, 'r') as fp:
            sr_data = json.load(fp)

        for post in sr_data['data']['children']:
            if post['kind'] == 't3':
                url = Url(post['data']['url'])
                directory, filename = get_path_from_url(pages_dir, url)
                page_path = os.path.join(directory, filename)

                if os.path.exists(page_path):
                    print 'Removing: %s' % page_path
                    # Remove the stored page
                    os.remove(page_path)

        # Remove the subreddit json file when done
        os.remove(abs_json_path)

    # Remove the actual subreddit dir
    os.removedirs(sr_json_dir)
