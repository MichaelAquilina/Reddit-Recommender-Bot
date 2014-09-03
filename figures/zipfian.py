from __future__ import division

from nltk.corpus import brown as corpus
from matplotlib import pyplot as plt
from collections import Counter

print('Counting term frequencies...')

word_counter = Counter()
for word in corpus.words():
    word_counter[word.lower()] += 1

print(word_counter.most_common(20))
print('%d Unique Terms' % len(word_counter))

n = len(word_counter)

# Generate the coordinates for plotting
y = [b for (a, b) in word_counter.most_common()]

plt.figure(1, figsize=(12, 5))

plt.yscale('log')
plt.xscale('log')

plt.xlabel('rank')
plt.ylabel('term frequency')

plt.scatter(range(n), y, edgecolors='none')
plt.plot(range(1, n), [y[0] / x for x in range(1, n)], color='red', linewidth='2.0', label='~1/x')
plt.legend()

plt.title('Zipfian Distribution')
plt.tight_layout()
plt.show()
