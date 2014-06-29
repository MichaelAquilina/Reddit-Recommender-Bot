#! /usr/bin/python

import os
import json

from url import Url
from utils import get_path_from_url, search_files


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


def clean_data(path):
    pages_dir = os.path.join(path, 'pages')
    subreddits_dir = os.path.join(path, 'subreddits')

    all_pages = set(search_files(pages_dir))
    referenced = set()

    for sr in os.listdir(subreddits_dir):
        sr_json_dir = os.path.join(subreddits_dir, sr)
        for json_file in os.listdir(sr_json_dir):
            with open(os.path.join(sr_json_dir, json_file), 'r') as fp:
                data = json.load(fp)

            for post in data['data']['children']:
                url = Url(post['data']['url'])
                directory, filename = get_path_from_url(pages_dir, url)
                referenced.add(os.path.join(directory, filename))

    count = 0
    unreferenced = all_pages - referenced
    for page_path in unreferenced:
        if os.path.exists(page_path):
            print 'Removing: %s' % page_path
            os.remove(page_path)
            parent = os.path.dirname(page_path)
            count += 1

            if len(os.listdir(parent)) == 0:
                os.removedirs(parent)

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
        count = clean_data(args.path)
        print 'Successfully deleted %d unreferenced pages' % count
