import json
import os
import requests
import urlparse

# Max listing limit as specified by the devapi
MAX_LIMIT = 100


def download_page(save_dir, url):
    """
    Downloads from the specified url, ignoring all non-text content. Files are saved
    to the specified save_dir and organised into folders according to the hostname. File
    names are extracted from the path with '/' characters replaced by '_'
    :param save_dir: Directory to save the downloaded file to.
    :param url: url from which to download
    """

    # Check encoding information before downloading everything
    req = requests.head(url)

    # Only download text content, we don't want anything else
    if req.ok and req.status_code == 200 and 'text' in req.headers['content-type']:
        # Perform the actual download
        req = requests.get(url)

        url = urlparse.urlparse(url)
        save_dir = os.path.join(save_dir, url.hostname)

        if not os.path.exists(save_dir):
            os.mkdir(save_dir)

        file_name = url.path.strip('/').replace('/', '_')
        file_path = os.path.join(save_dir, file_name)

        if not file_path.endswith('.html'):
            file_path += '.html'

        with open(file_path, 'w') as f:
            f.write(req.text.encode('utf8'))


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Downloads top post data from a specified subreddit')
    parser.add_argument('subreddit', type=str, help='Name of the subreddit to retrieve posts from')
    parser.add_argument('--limit', type=int, default=25, help='Number of submissions to retrieve')
    parser.add_argument('--out', type=str, default='', help='Path to store incoming JSON files')
    parser.add_argument('--period', choices=('year', 'month', 'week', 'all'), default='all')

    args = parser.parse_args()

    # Create the save path if it does not exist
    if not os.path.exists(args.out):
        os.mkdir(args.out)

    if not os.path.isdir(args.out):
        print 'Out parameter must be a directory'
    else:
        # Amount of requests required based on the limit specified
        count = args.limit
        i = 0

        # After pointer for retrieving next batch of submissions
        after = None

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
                'http://www.reddit.com/r/{}/top.json'.format(args.subreddit),
                headers={'user-agent': 'postextractor'},
                params=params
            )

            if r.ok:
                submission_data = r.json()

                # Detect if no data is returned before continuing
                if len(submission_data['data']['children']) == 0:
                    print 'The subreddit \'{}\' does not exist'.format(args.subreddit)
                    break

                for post in submission_data['data']['children']:
                    print post['data']['title']

                    # This should be threaded!
                    if not post['data']['is_self']:
                        download_page(args.out, post['data']['url'])

                after = submission_data['data']['after']
                count -= len(submission_data['data']['children'])

                save_path = os.path.join(args.out, '{}.{}.json'.format(args.subreddit, i))

                with open(save_path, 'w') as f:
                    json.dump(submission_data, f, indent=4)

                i += 1
            else:
                print 'An Error occurred'
                break
