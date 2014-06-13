#! /usr/bin/python

import json
import os
import requests
import urlparse

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


def download_html_page(target_dir, page_url, timeout=15):

    # Check encoding information before downloading everything
    req = requests.head(page_url, timeout=timeout)

    # Only download text content, we don't want anything else
    if req.ok and \
       req.status_code == 200 and \
       'content-type' in req.headers and \
       'text/html' in req.headers['content-type']:

        # Perform the actual download
        req = requests.get(page_url, timeout=timeout)

        page_url = urlparse.urlparse(page_url)
        page_save_dir = os.path.join(target_dir, page_url.hostname)

        if not os.path.exists(page_save_dir):
            os.mkdir(page_save_dir)

        # Create subdirs according to the url path
        url_path = page_url.path.strip('/')

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

    parser = argparse.ArgumentParser(description='Downloads top url posts from a specified subreddit along with their pages')
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

        file_index = 0  # Current Index of json file to be saved
        post_index = 0  # Current Index of post being processed

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

                save_path = os.path.join(save_dir, '{}.{}.{}.json'.format(args.subreddit, args.filter, file_index))

                with open(save_path, 'w') as f:
                    json.dump(subreddit_data, f, indent=4)

                # Detect if no data is returned before continuing
                if len(subreddit_data['data']['children']) == 0:
                    print 'The subreddit \'%s\' does not exist', args.subreddit
                    break

                for post in subreddit_data['data']['children']:

                    if page_count <= 0:
                        break

                    post_index += 1

                    if not post['data']['is_self']:

                        url = post['data']['url']
                        title = post['data']['title']

                        print u'{}: {} ({})'.format(args.limit - page_count + 1, title, url)

                        try:
                            success = download_html_page(pages_dir, url, timeout=15)
                        except requests.ConnectionError:
                            print 'Unable to connect to: %s' % url
                        except requests.Timeout:
                            print 'Timeout on: %s' % url
                        except Exception as e:
                            print 'A generic error occurred on: %s' % url
                            print e.message
                        else:
                            page_count -= success

                # Set the after token for the next batch of data to download
                after = subreddit_data['data']['after']

                file_index += 1
            else:
                print 'An error has occurred while communicating with the Reddit API'
                break

        print 'Successfully downloaded %s HTML pages' % args.limit
