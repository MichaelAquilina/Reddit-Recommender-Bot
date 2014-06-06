#! /usr/bin/python

import json
import os
import requests
import urlparse
import threading
import time
import logging

# Max listing limit as specified by the reddit devapi
MAX_LIMIT = 100


class PageDownloader(threading.Thread):
    """
    Worker thread that reads from a given page queue and downloads from the
    specified urls using the page_download method.
    """

    def __init__(self, page_queue, lock, pages_dir):
        self.running = True
        self.page_queue = page_queue
        self.lock = lock
        self.pages_dir = pages_dir
        super(PageDownloader, self).__init__()

    def run(self):
        while self.page_queue or self.running:

            self.lock.acquire()
            if len(self.page_queue) > 0:

                url = self.page_queue[0]
                del self.page_queue[0]
                self.lock.release()

                try:
                    download_page(self.pages_dir, url)
                except requests.ConnectionError as e:
                    logging.warn('Unable to connect to: %s (%s)', url, e.message)
                except requests.Timeout as e:
                    logging.warn('Received a timeout from: %s (%s)', url, e.message)
                except Exception as e:
                    logging.error('A generic error has occurred while downloading: %s %s', url, e.message)
            else:
                self.lock.release()

            # Thread should sleep
            time.sleep(0.1)


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


def download_page(save_dir, url):
    """
    Downloads from the specified url, ignoring all non-text content. Files are saved
    to the specified save_dir and organised into folders according to the hostname. File
    names are extracted from the path with '/' characters replaced by '_'
    :param save_dir: Directory to save the downloaded file to.
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
        save_dir = os.path.join(save_dir, url.hostname)

        if not os.path.exists(save_dir):
            os.mkdir(save_dir)

        # Standard html encoding for urls
        file_name = url.path.strip('/').replace('/', '%2F')

        if file_name == '':
            file_name = 'index.html'

        file_path = os.path.join(save_dir, file_name)

        if not file_path.endswith('.html'):
            file_path += '.html'

        with open(file_path, 'w') as f:
            f.write(req.text.encode('utf8'))


if __name__ == '__main__':

    import argparse
    import progressbar

    parser = argparse.ArgumentParser(description='Downloads top post data from a specified subreddit')
    parser.add_argument('subreddit', type=str, help='Name of the subreddit to retrieve posts from')
    parser.add_argument('--limit', type=int, default=25, help='Number of submissions to retrieve')
    parser.add_argument('--out', type=str, default='', help='Path to store incoming JSON files')
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

        # Setup downloader threads
        page_queue = []
        downloaders = []
        lock = threading.Lock()
        pages_dir = join_and_check(args.out, 'pages')

        for i in xrange(args.threads):
            d = PageDownloader(page_queue, lock, pages_dir)
            downloaders.append(d)
            d.start()

        # Amount of requests required based on the limit specified
        count = args.limit
        i = 0
        index = 0

        # Determine the save directory
        save_dir = join_and_check(args.out, 'subreddits', args.subreddit)

        while count:

            # Request data
            params = {
                'limit': min(count, MAX_LIMIT),
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
                submission_data = r.json()

                save_path = os.path.join(save_dir, '{}.{}.json'.format(args.subreddit, i))

                with open(save_path, 'w') as f:
                    json.dump(submission_data, f, indent=4)

                # Detect if no data is returned before continuing
                if len(submission_data['data']['children']) == 0:
                    logging.warn('The subreddit \'%s\' does not exist', args.subreddit)
                    break

                for post in submission_data['data']['children']:
                    print u'{}: {}'.format(index, post['data']['title'])
                    index += 1

                    if not post['data']['is_self']:
                        lock.acquire()
                        page_queue.append(post['data']['url'])
                        lock.release()

                after = submission_data['data']['after']
                count -= len(submission_data['data']['children'])

                i += 1
            else:
                logging.error('An error has occurred while communicating with the Reddit API')
                break

        print '-----------------------------------------------'
        print 'Waiting for the downloader threads to finish...'

        for d in downloaders:
            d.running = False

        # Use a progress bar to let the user know how far along the process is
        start = len(page_queue)
        pb = progressbar.ProgressBar()
        pb.start()

        while page_queue:
            pb.update((start - len(page_queue)) / float(start) * 100)
            time.sleep(0.1)

        pb.finish()

        print 'Almost ready...waiting for final downloads to complete'

        # Wait for all the threads to finish before completing
        for d in downloaders:
            d.join()
