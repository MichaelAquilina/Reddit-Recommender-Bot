#! /usr/bin/python

import json
import os
import requests
import urlparse
import time
import logging

# Max listing limit as specified by the Reddit devapi
MAX_LIMIT = 100


def join_and_check(path, *paths):
    """
    Joins the specified path using os.path.join and ensures it exists. It then
    checks to see if the specified path is a directory and if not raises a
    ValueError specifying the issue.
    :param path: path with which to join other paths
    :param paths: further paths to join to the original path
    :return: joint path
    """
    result = os.path.join(path, *paths)

    if not os.path.exists(result):
        os.makedirs(result)

    if not os.path.isdir(result):
        raise ValueError('{} is a file but needs to be a directory'.format(result))
    else:
        return result


def download_page(target_dir, url):
    """
    Downloads from the specified url, ignoring all non-text content. Files are saved
    to the specified save_dir and organised into folders according to the hostname. File
    names are extracted from the path with '/' characters replaced by '_'
    :param target_dir: Directory to save the downloaded file to.
    :param url: url from which to download
    """

    # Check encoding information before downloading everything
    req = requests.head(url, timeout=15)

    # Only download text content, we don't want anything else
    if req.ok and \
       req.status_code == 200 and \
       'content-type' in req.headers and \
       'text' in req.headers['content-type']:

        # Perform the actual download
        req = requests.get(url, timeout=15)

        url = urlparse.urlparse(url)
        page_save_dir = os.path.join(target_dir, url.hostname)

        if not os.path.exists(page_save_dir):
            os.mkdir(page_save_dir)

        # Create subdirs according to the url path
        url_path = url.path.strip('/')
        path_index = url_path.rfind('/')
        if path_index != -1:
            sub_path = url_path[:path_index].lstrip('/')
            page_save_dir = os.path.join(page_save_dir, sub_path)

            if not os.path.exists(page_save_dir):
                os.makedirs(page_save_dir)

            file_name = url_path[path_index:].strip('/')
        else:
            file_name = url_path

        # Root page directories are "index.html"
        if file_name == '':
            file_name = 'index.html'

        file_path = os.path.join(page_save_dir, file_name)

        with open(file_path, 'w') as fp:
            fp.write(req.text.encode('utf8'))

        return 1
    else:
        return 0


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Downloads top post data from a specified subreddit')
    parser.add_argument('subreddit', type=str, help='Name of the subreddit to retrieve posts from')
    parser.add_argument('out', type=str, help='Path to store incoming JSON files')
    parser.add_argument('--limit', type=int, default=25, help='Number of submissions to retrieve')
    parser.add_argument('--period', choices=('year', 'month', 'week', 'all'), default='year')
    parser.add_argument('--threads', type=int, default=10)
    parser.add_argument('--filter', type=str, choices=('top', 'controversial'), default='top')

    args = parser.parse_args()

    # Create the save path if it does not exist
    if not os.path.exists(args.out):
        os.mkdir(args.out)

    if not os.path.isdir(args.out):
        print 'Out parameter must be a directory'
    else:
        # After pointer for retrieving next batch of submissions
        after = None

        # Amount of requests required based on the limit specified
        page_count = args.limit

        # Target directory to save the downloaded pages
        pages_dir = join_and_check(args.out, 'pages')

        i = 0
        index = 0

        # Determine the save directory
        save_dir = join_and_check(args.out, 'subreddits', args.subreddit)

        while page_count:

            # Request data
            params = {
                'limit': MAX_LIMIT,
                'after': after,
                'show': 'all',
                't': args.period,
            }

            # Request top posts in JSON format
            r = requests.get(
                'http://www.reddit.com/r/{}/{}.json'.format(args.subreddit, args.filter),
                headers={'user-agent': 'postextractor'},
                params=params
            )

            if r.ok:
                # Data returned is in JSON format
                subreddit_data = r.json()

                save_path = os.path.join(save_dir, '{}.{}.{}.json'.format(args.subreddit, args.filter, i))

                with open(save_path, 'w') as f:
                    json.dump(subreddit_data, f, indent=4)

                # Detect if no data is returned before continuing
                if len(subreddit_data['data']['children']) == 0:
                    logging.warn('The subreddit \'%s\' does not exist', args.subreddit)
                    break

                for post in subreddit_data['data']['children']:

                    if page_count <= 0:
                        break

                    print u'{}: {}'.format(args.limit - page_count + 1, post['data']['title'])
                    index += 1

                    if not post['data']['is_self']:
                        url = post['data']['url']
                        try:
                            success = download_page(pages_dir, url)
                        except requests.ConnectionError:
                            print 'Unable to connect to: %s' % url
                        except requests.Timeout:
                            print 'Timeout on: %s' % url
                        except Exception as e:
                            print 'A generic error occurred on: %s' % url
                            print e.message
                        else:
                            page_count -= success

                after = subreddit_data['data']['after']

                i += 1
            else:
                logging.error('An error has occurred while communicating with the Reddit API')
                break
