#! /usr/bin/python

import os
import json

from url import Url
from utils import get_path_from_url


# BUG: Pages referenced by more than 1 subreddit will still be deleted by the remove command
def remove_subreddit(path, subreddit):
    sr_json_dir = os.path.join(path, 'subreddits', subreddit)
    pages_dir = os.path.join(path, 'pages')

    if not os.path.exists(sr_json_dir):
        return 0

    count = 0

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
                    count += 1

                    # Remove leaf directory and all empty intermediate ones
                    if len(os.listdir(directory)) == 0:
                        os.removedirs(directory)

        # Remove the subreddit json file when done
        os.remove(abs_json_path)

    # Remove the actual subreddit dir
    os.removedirs(sr_json_dir)
    return count


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='Data Store Tool for clearing and maintaining data')
    parser.add_argument('path', help='Path of the Data Store on which to operate on', type=str)

    subparsers = parser.add_subparsers(dest='command')

    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Detect unreferenced pages and remove them')

    # Remove Command
    remove_parser = subparsers.add_parser('remove', help='Remove the specified subreddit and all its associated pages')
    remove_parser.add_argument('subreddit', help='Target subreddit to remove', type=str)

    args = parser.parse_args()

    if args.command == 'remove':
        count = remove_subreddit(args.path, args.subreddit)
        print 'Successfully deleted %d pages' % count
    elif args.command == 'clean':
        print 'Clean Command'
