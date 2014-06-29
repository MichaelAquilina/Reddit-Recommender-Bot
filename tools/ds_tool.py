#! /usr/bin/python

__about__ = \
    """
    Data Store Tool for viewing, removing and maintaining data available in a Reddit Data Store.
    """

import os
import json

from url import Url
from utils import get_path_from_url, search_files


# Lists all page files referenced in the subreddit JSON file
def get_subreddit_files(pages_dir, subreddits_dir, subreddit):
    results = []

    sr_json_dir = os.path.join(subreddits_dir, subreddit)
    for json_file in os.listdir(sr_json_dir):
        with open(os.path.join(sr_json_dir, json_file), 'r') as fp:
            data = json.load(fp)

        for post in data['data']['children']:
            url = Url(post['data']['url'])
            directory, filename = get_path_from_url(pages_dir, url)
            results.append(os.path.join(directory, filename))

    return results


# BUG: Pages referenced by more than 1 subreddit will still be deleted by the remove command
def remove_subreddit(path, subreddit):
    subreddits_dir = os.path.join(path, 'subreddits')
    pages_dir = os.path.join(path, 'pages')

    count = 0

    for file_path in get_subreddit_files(pages_dir, subreddits_dir, subreddit):
        print 'Removing: %s' % file_path
        # Remove the stored page
        os.remove(file_path)
        count += 1
        parent = os.path.dirname(file_path)

        # Remove leaf directory and all empty intermediate ones
        if len(os.listdir(parent)) == 0:
            os.removedirs(parent)

    # Remove the subreddit json files when done
    sr_json_dir = os.path.join(subreddits_dir, subreddit)
    if os.path.exists(sr_json_dir):
        for json_file in os.listdir(sr_json_dir):
            abs_json_path = os.path.join(sr_json_dir, json_file)
            os.remove(abs_json_path)

        # Remove the actual subreddit dir
        os.removedirs(sr_json_dir)

    return count


def clean_data(path):
    pages_dir = os.path.join(path, 'pages')
    subreddits_dir = os.path.join(path, 'subreddits')

    all_pages = set(search_files(pages_dir))
    referenced = set()

    for subreddit in os.listdir(subreddits_dir):
        for file_path in get_subreddit_files(pages_dir, subreddits_dir, subreddit):
            referenced.add(file_path)

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


def count_data(path, subreddit):
    pages_dir = os.path.join(path, 'pages')
    subreddits_dir = os.path.join(path, 'subreddits')

    if subreddit == 'all':
        return len(list(search_files(pages_dir)))
    else:
        return len(get_subreddit_files(pages_dir, subreddits_dir, subreddit))


def list_subreddits(path):
    subreddits_dir = os.path.join(path, 'subreddits')
    return os.listdir(subreddits_dir)


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description=__about__)
    subparsers = parser.add_subparsers(dest='command')
    parser.add_argument('path', help='Path of the Data Store on which to operate on', type=str)

    # List command
    list_parser = subparsers.add_parser('list', help='List available subreddits')

    # Count command
    count_parser = subparsers.add_parser('count', help='Count the number of pages')
    count_parser.add_argument('subreddit', help='Subreddit for which to count. Specify \'all\' for no filter')

    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Detect unreferenced pages and remove them')

    # Remove Command
    remove_parser = subparsers.add_parser('remove', help='Remove the specified subreddit and all its associated pages')
    remove_parser.add_argument('subreddit', help='Target subreddit to remove', type=str)

    args = parser.parse_args()

    if args.command == 'remove':
        print 'Successfully deleted %d pages' % remove_subreddit(args.path, args.subreddit)
    elif args.command == 'clean':
        print 'Successfully deleted %d unreferenced pages' % clean_data(args.path)
    elif args.command == 'count':
        pages_count = count_data(args.path, args.subreddit)
        if args.subreddit == 'all':
            print '%d pages found' % pages_count
        else:
            print '\'%s\' has %d referenced pages available' % (args.subreddit, pages_count)

    elif args.command == 'list':
        print list_subreddits(args.path)
