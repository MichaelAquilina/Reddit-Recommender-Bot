__about__ = """
    Parse an Open Directory Project (ODP) contents file and extracts the urls to be placed in a list.
    The data can then be stored accordingly to how one sees fit. Data from the list can be randomly
    accessed for random samples on the web. Part of the Reddit Recommender Bot project for generating
    unlabeled data.
"""

import gzip

# IMPORTANT NOTE:
# My impressions re that the list of websites provided by this list are quite shitty
# Apart from the fact they are not all english, a lot of sites are garbage and are numerous
# within the list meaning a random sample is likely to pick them up. A lot of the sites
# listed are also no longer available or display error codes when visited

# TODO: Loads of cleaning up to do
# TODO: Remove any hard coded information


# Returns the indices of the specified character in the string
def indices(line, key):
    result = []
    for index, c in enumerate(line):
        if c == key:
            result.append(index)

    return result


if __name__ == '__main__':

    import time

    # TODO: Remove this hard coded path
    save_path = '/home/michaela/Development/urllist.txt.gz'
    path = '/home/michaela/Development/content.rdf.u8.gz'
    count = 0

    t0 = time.time()
    urls = list()

    with gzip.GzipFile(path, mode='r') as fp:
        data = fp.readline()
        while data:
            # Simple Heuristic that should work to identify urls
            if '<link ' in data:
                start, end = indices(data, '"')
                url = data[start + 1:end]
                urls.append(url)

                count += 1

            if count % 5000 == 0:
                print count

            # Read next line
            data = fp.readline()

    print 'Done'
    print 'Runtime = {}'.format(time.time() - t0)

    # Smaller set is an implication that there is duplicate data!!!
    print len(urls)
    print len(set(urls))

    # Randomly Sample 100 web pages
    import random
    for i in xrange(1000):
        index = random.randint(0, len(urls))
        print urls[index]

    # Save to a simple list of urls in a compressed text file
    with gzip.GzipFile(save_path, mode='w') as fp:
        for url in urls:
            fp.write('%s\n' % url)

    print 'Done Saving'
