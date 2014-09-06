from __future__ import division, print_function

import requests

from bs4 import BeautifulSoup
from url import Url

domain_blacklist = frozenset([
    'youtube.com', 'imgur.com', 'i.imgur.com',
    'vimeo.com', 'picasa.google.com', 'tinypic.com',
    'xkcd.com', 'smbc-comics.com', 'flickr.com',
    'reddit.com', 'youtu.be', 'flic.kr', 'pyvideo.org',
    'londonreal.tv',
])

# Assumes the variables 'pages' and 'visited' are global


def add_contained_urls(target_url):
    try:
        req = requests.get(target_url.geturl())

        if req and req.ok:
            soup = BeautifulSoup(req.text, 'lxml')
            for anchor in soup.find_all('a'):
                if 'href' in anchor.attrs:
                    new_url = Url(anchor.attrs['href'])

                    if new_url.hostname is None:
                        new_url.hostname = target_url.hostname

                    if new_url.hostname in domain_blacklist:
                        continue

                    if new_url not in visited:
                        pages.append(new_url)
                        visited.add(new_url)
                        print(new_url)
    except requests.ConnectionError:
        print('Unable to connect to %s' % target_url.geturl())


# populate the initial seed list using the top subreddit posts
def add_all_subreddit_posts(subreddit):
    # Should first download all subreddit posts and add them to the visited list
    # This is much faster than individually checking if a page has been added
    after = None
    while True:
        params = {
            'limit': 100,
            'after': after,
            'show': 'all',
            't': 'all',
        }

        r = requests.get(
            'http://www.reddit.com/r/%s/top.json' % subreddit,
            headers={'user-agent': 'python-webcrawler'},
            params=params
        )

        if r and r.ok:
            subreddit_data = r.json()

            for post in subreddit_data['data']['children']:
                if post['kind'] == 't3' and not post['data']['is_self']:
                    post_url = Url(post['data']['url'])
                    add_contained_urls(post_url)

            after = subreddit_data['data']['after']
            if after is None:
                break

if __name__ == '__main__':

    pages = []
    visited = set()

    print('Adding all posted subreddit pages to visited list')
    add_all_subreddit_posts('python')

    print('Beginning web crawling')

    while True:
        page_url = pages[0]
        pages = pages[1:]
        add_contained_urls(page_url)
