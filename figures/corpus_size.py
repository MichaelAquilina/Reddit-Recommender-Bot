from __future__ import print_function

import os
import random
import nltk
import json
import time
import bz2

from matplotlib import pyplot as plt

from textparser import word_tokenize
from utils import search_files, load_db_params
from index.hashedindex import HashedIndex
from index.wikiindex import WikiIndex

plt.title('Dimension growth with relation to corpus size')

plt.ylabel('Number of Dimensions')
plt.xlabel('Corpus Size')

data_path = '/home/michaela/Development/Reddit-Testing-Data'
pages_path = os.path.join(data_path, 'pages')

available_pages = set(search_files(pages_path))
sample_sizes = (400, 600, 800, 1000, 1200)


def test_wiki_index(cache_name, sample_set, sample_sizes, word_concepts_ags, db_params, n_concepts=10):
    dimensions = []
    runtimes = []

    if not os.path.exists('.cache'):
        os.mkdir('.cache')

    for n_samples in sample_sizes:
        # Check if a cached version is available
        file_name = '.cache/%s_%d.json.bz2' % (cache_name, n_samples)
        if os.path.exists(file_name):
            print('Found cached version of %s (%d)' % (cache_name, n_samples))
            with bz2.BZ2File(file_name, 'r') as fp:
                loaded_data = json.load(fp)

            concepts = loaded_data['concepts']
            run = loaded_data['runtime']
        else:
            wiki = WikiIndex(**db_params)
            concepts = set()

            print('Running index on %s (%d)' % (cache_name, n_samples))
            t0 = time.time()
            for index, page in enumerate(sample_set[:n_samples]):
                with open(page, 'r') as fp:
                    html_text = fp.read()

                results, _, _ = wiki.word_concepts(html_text, **word_concepts_ags)
                for c in results[:n_concepts]:
                    concepts.add(c.page_id)

            run = time.time() - t0

            with bz2.BZ2File(file_name, 'w') as fp:
                json.dump({
                    'concepts': list(concepts),
                    'runtime': run,
                }, fp, indent=5)

        runtimes.append(run)
        dimensions.append(len(concepts))

    return dimensions, runtimes


def test_hashed_index(cache_name, sample_set, sample_sizes, tokenize_args, prune, prune_args):
    dimensions = []
    runtimes = []

    if not os.path.exists('.cache'):
        os.mkdir('.cache')

    for n_samples in sample_sizes:
        bow = HashedIndex()

        # Check if a cached version is available
        file_name = '.cache/%s_%d.json.bz2' % (cache_name, n_samples)
        if os.path.exists(file_name):
            print('Found cached version of %s (%d)' % (cache_name, n_samples))
            with bz2.BZ2File(file_name, 'r') as fp:
                loaded_data = json.load(fp)

            bow.from_dict(loaded_data['index'])
            run = loaded_data['runtime']
        else:
            print('Running index on %s (%d)' % (cache_name, n_samples))
            t0 = time.time()
            for index, page in enumerate(sample_set[:n_samples]):
                with open(page, 'r') as fp:
                    html_text = fp.read()

                doc_name = str(index)  # Use a pseudo doc name for speed
                for term in word_tokenize(html_text, **tokenize_args):
                    bow.add_term_occurrence(term, doc_name)

            if prune:
                bow.prune(**prune_args)

            run = time.time() - t0

            # Save to storage for fast loading
            with bz2.BZ2File(file_name, 'w') as fp:
                json.dump({
                    'runtime': run,
                    'index': bow.to_dict(),
                }, fp, indent=5)

        dimensions.append(len(bow.terms()))
        runtimes.append(run)

    return dimensions, runtimes

if __name__ == '__main__':

    plot_params = {
        'linewidth': 2,
    }

    # Always use the same random seed
    sample_set = random.sample(available_pages, max(sample_sizes))

    print('Plain Bag of Words')
    dimension_sizes, runtimes = test_hashed_index(
        'bow',
        sample_set, sample_sizes,
        {'remove_urls': True},
        False, None
    )
    plt.plot(sample_sizes, dimension_sizes, label='BoW', **plot_params)

    print('Bag of Words with Porter Stemmer')
    dimension_sizes, runtimes = test_hashed_index(
        'bow_porter',
        sample_set, sample_sizes,
        {'remove_urls': True, 'stemmer': nltk.PorterStemmer()},
        False, None
    )
    plt.plot(sample_sizes, dimension_sizes, label='BoW Porter', **plot_params)

    print('Bag of Words with Lancaster Stemmer')
    dimension_sizes, runtimes = test_hashed_index(
        'bow_lancaster',
        sample_set, sample_sizes,
        {'remove_urls': True, 'stemmer': nltk.LancasterStemmer()},
        False, None
    )
    plt.plot(sample_sizes, dimension_sizes, label='BoW Lancaster', **plot_params)

    print('Bag of Words with Pruning')
    dimension_sizes, runtimes = test_hashed_index(
        'bow_prune',
        sample_set, sample_sizes,
        {'remove_urls': True},
        True, {}
    )
    plt.plot(sample_sizes, dimension_sizes, label='BoW Pruned', **plot_params)

    params = load_db_params('wsd.db.json')

    print('Bag of Concepts')
    dimension_sizes, runtimes = test_wiki_index(
        'boc',
        sample_set, sample_sizes,
        {},
        params,
        n_concepts=10
    )
    plt.plot(sample_sizes, dimension_sizes, label='BoC', **plot_params)

    #plt.yscale('log')
    plt.xticks(sample_sizes)

    plt.tight_layout(pad=0.5)
    plt.legend(loc='upper left')
    plt.show()
