import json
import os
import requests

# Max listing limit as specified by the devapi
MAX_LIMIT = 100

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

            after = submission_data['data']['after']
            count -= len(submission_data['data']['children'])

            save_path = os.path.join(args.out, '{}.{}.json'.format(args.subreddit, i))

            with open(save_path, 'w') as f:
                json.dump(submission_data, f, indent=4)

            i += 1
        else:
            print 'An Error occurred'
            break
