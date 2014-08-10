from nltk.corpus import inaugural as corpus
from matplotlib import pyplot as plt
from collections import Counter

word_counter = Counter()
for word in corpus.words():
    word_counter[word.lower()] += 1

print('%d Unique Terms' % len(word_counter))

# Generate the coordinates for plotting
x = range(len(word_counter))
y = [b for (a, b) in word_counter.most_common()]

ax = plt.axes(xlim=(0, 800), ylim=(0, 2500), xmargin=0, ymargin=0)

ax.fill_between(x, y)

plt.show()
