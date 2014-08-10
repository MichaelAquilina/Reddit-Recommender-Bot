# Based off the work of Jake DVP

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

from utils import plot_svc_decision_function

from sklearn.datasets.samples_generator import make_blobs
X, y = make_blobs(n_samples=80, centers=2, cluster_std=0.60, random_state=7657)
plt.scatter(X[:, 0], X[:, 1], c=y, s=50)

from sklearn.svm import SVC
classifier = SVC(kernel='linear')
classifier.fit(X, y)

plt.scatter(X[:, 0], X[:, 1], c=y, s=80)
plot_svc_decision_function(classifier, plt)

cm_bright = ListedColormap(['#FF0000', '#0000FF'])

# Plot the support vectors
plt.scatter(X[:, 0], X[:, 1], c=y, s=80, cmap=cm_bright)
plot_svc_decision_function(classifier, plt)
plt.scatter(classifier.support_vectors_[:, 0], classifier.support_vectors_[:, 1],
            s=200, facecolors='none')

plt.gcf().canvas.set_window_title('svm')

plt.tight_layout()
plt.show()
