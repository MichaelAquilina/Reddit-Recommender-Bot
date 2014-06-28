#! /usr/bin/python

import json
import os
import requests
import threading
import Queue

from url import Url
from utils import get_path_from_url

# Max listing limit as specified by the Reddit devapi
MAX_LIMIT = 100


# List of domains which should be ignored
domain_blacklist = frozenset([
    'youtube.com', 'imgur.com', 'i.imgur.com',
    'vimeo.com', 'picasa.google.com', 'tinypic.com',
    'xkcd.com', 'smbc-comics.com', 'flickr.com',
])

MAX_LENGTH = 1 * 1024 * 1024  # Max 1mb size
MIN_LENGTH = 1024             # Min 1kb size


class DownloaderThread(threading.Thread):

    def __init__(self):
        self.running = True
        super(DownloaderThread, self).__init__()

    def run(self):
        global page_queue, pages_dir, page_lock, page_count, page_limit
        self.running = True

        while self.running:
            try:
                url, title = page_queue.get(timeout=0.1)
            except Queue.Empty:
                continue

            try:
                req = download_html_page(url.geturl(), timeout=8)

                if req and MIN_LENGTH < len(req.text) < MAX_LENGTH:
                    directory, filename = get_path_from_url(pages_dir, url)

                    if not os.path.exists(directory):
                        os.makedirs(directory)

                    with open(os.path.join(directory, filename), 'w') as fp:
                        fp.write(req.text.encode('utf8'))

                    page_lock.acquire()
                    page_count -= 1
                    print u'[{}]: {} ({})'.format(page_limit - page_count, title, url.geturl())
                    page_lock.release()

            except requests.ConnectionError:
                print 'Unable to connect to: %s' % url
            except requests.Timeout:
                print 'Timeout on: %s' % url
            except IOError:
                print 'IOError on: %s' % url
            except Exception as e:
                print 'A generic error occurred on: %s' % url
                print e.message

            # Always mark the task as done before moving on the next item
            page_queue.task_done()


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


def download_html_page(page_url, timeout=8):
    # Check encoding information before downloading everything
    req = requests.head(page_url, timeout=timeout, allow_redirects=True)

    # Only download text content, we don't want anything else
    if req.ok and \
       req.status_code == 200 and \
       'content-type' in req.headers and \
       'text/html' in req.headers['content-type']:

        # Perform the actual download
        req = requests.get(page_url, timeout=timeout, allow_redirects=True)

        return req
    else:
        return None


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Downloads top url posts from a specified subreddit along with their pages')
    parser.add_argument('subreddit', type=str, help='Name of the subreddit to retrieve posts from')
    parser.add_argument('out', type=str, help='Path to store incoming JSON files')
    parser.add_argument('--limit', type=int, default=25, help='Number of submissions to retrieve')
    parser.add_argument('--period', choices=('year', 'month', 'week', 'all'), default='all')
    parser.add_argument('--filter', type=str, choices=('top', 'controversial'), default='top')
    parser.add_argument('--threads', type=int, default=10, help='Number of Threads to download with')

    args = parser.parse_args()

    # Create the save path if it does not exist
    if not os.path.exists(args.out):
        os.mkdir(args.out)

    if args.threads > 100:
        print 'WARNING: Using more than 100 threads has no benefit'
        print 'Setting --threads 100'
        args.threads = 100

    if not os.path.isdir(args.out):
        print 'Out parameter must be a directory'
    else:
        # After pointer for retrieving next batch of submissions
        after = None

        page_queue = Queue.Queue()
        page_lock = threading.Lock()

        # Amount of requests required based on the limit specified
        page_count = args.limit
        page_limit = args.limit
        local_count = args.limit

        # Target directory to save the downloaded pages
        pages_dir = join_and_check(args.out, 'pages')

        page_threads = []
        for _ in xrange(args.threads):
            t = DownloaderThread()
            page_threads.append(t)
            t.start()

        file_index = 0  # Current Index of json file to be saved
        post_index = 0  # Current Index of post being processed

        # Determine the save directory
        save_dir = join_and_check(args.out, 'subreddits', args.subreddit)

        # Keep track of visited pages to prevent duplicates
        visited = set()

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

                save_path = os.path.join(save_dir, '{}.{}.{}.json'.format(args.subreddit, args.filter, file_index))

                # Detect if no data is returned before continuing
                if len(subreddit_data['data']['children']) == 0:
                    print 'The subreddit \'%s\' does not exist', args.subreddit
                    break

                with open(save_path, 'w') as f:
                    json.dump(subreddit_data, f, indent=4)

                for post in subreddit_data['data']['children']:

                    if local_count <= 0:
                        # TODO: this can probably be improved
                        # Currently causes a slow down towards end of execution
                        page_queue.join()
                        local_count = page_count
                        if local_count <= 0:
                            break

                    post_index += 1

                    if post['kind'] == 't3':

                        url = Url(post['data']['url'])
                        title = post['data']['title']

                        if url.hostname in domain_blacklist:
                            continue

                        if url not in visited:
                            visited.add(url)
                            local_count -= 1
                            page_queue.put((url, title))

                # Set the after token for the next batch of data to download
                after = subreddit_data['data']['after']

                file_index += 1
            else:
                print 'An error has occurred while communicating with the Reddit API'
                break

        # Signify end of runtime and wait
        for t in page_threads:
            t.running = False
            t.join()

        print 'Successfully downloaded %d HTML pages (target was %d)' % (page_limit - page_count, args.limit)
