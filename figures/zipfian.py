from __future__ import division

from nltk.corpus import brown as corpus
from matplotlib import pyplot as plt
from collections import Counter

word_counter = Counter()
for word in corpus.words():
    word_counter[word.lower()] += 1

print(word_counter.most_common(20))
print('%d Unique Terms' % len(word_counter))

n = len(word_counter)

# Generate the coordinates for plotting
y = [b for (a, b) in word_counter.most_common()]

plt.scatter(range(n), y, edgecolors='none')
plt.plot(range(1, n), [y[0] / x for x in range(1, n)], color='red', linewidth='2.0', label='1/x')

plt.yscale('log')
plt.xscale('log')

plt.xlabel('rank')
plt.ylabel('term frequency')

plt.tight_layout()
plt.show()
