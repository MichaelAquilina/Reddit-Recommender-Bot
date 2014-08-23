from __future__ import print_function

from nltk.stem import PorterStemmer, LancasterStemmer, wordnet

word_list = {
    'runner': 'n',
    'running': 'v',
    'ran': 'v',
    'scientist': 'n',
    'science': 'n',
    'Maltese': 'a',
}

porter = PorterStemmer()
lancaster = LancasterStemmer()
lemmatiser = wordnet.WordNetLemmatizer()

for word, pos in word_list.items():
    print(word, end=' ')
    print(porter.stem(word), end=' ')
    print(lancaster.stem(word), end=' ')
    print(lemmatiser.lemmatize(word, pos=pos), end=' ')
    print()
