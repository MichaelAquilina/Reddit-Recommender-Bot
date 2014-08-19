import os
import math

from matplotlib import pyplot as plt
from collections import Counter
from goose import Goose, Configuration

from textparser import word_tokenize
from datasource import load_data_source

data_path = '/home/michaela/Development/Reddit-Testing-Data'
subreddit_list = ['python', 'science', 'programming', 'technology']

rows = int(math.ceil(len(subreddit_list) / 2.0))

figure, axes = plt.subplots(rows, 2)

for subreddit_index, subreddit in enumerate(subreddit_list):
    i = subreddit_index % 2
    j = subreddit_index / 2

    pages_path = os.path.join(data_path, 'pages')

    config = Configuration()
    config.enable_image_fetching = False
    config.use_meta_language = False
    goose = Goose(config)

    term_counter = Counter()

    for page_index, path in enumerate(load_data_source(data_path, subreddit, 0)):
        abs_path = os.path.join(pages_path, path)
        if os.path.exists(abs_path):
            print '(%d) %d: %s' % (subreddit_index, page_index, path)

            with open(abs_path, 'r') as fp:
                html_text = fp.read()

            article = goose.extract(raw_html=html_text)

            for term in word_tokenize(article.cleaned_text, remove_urls=True):
                term_counter[term] += 1

    print term_counter.most_common(20)

    n = 1500

    axes[i, j].set_xlim(0, n)
    axes[i, j].set_title(subreddit)
    axes[i, j].fill_between(xrange(n), [b for (a, b) in term_counter.most_common(n)])

figure.canvas.set_window_title('subreddits')

plt.tight_layout()
plt.show()
