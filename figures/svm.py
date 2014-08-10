# Based off the work of Jake DVP

import matplotlib.pyplot as plt
import numpy as np

from sklearn.datasets.samples_generator import make_blobs
X, y = make_blobs(n_samples=80, centers=2, cluster_std=0.60, random_state=7657)
plt.scatter(X[:, 0], X[:, 1], c=y, s=50)


def plot_svc_decision_function(clf):
    """Plot the decision function for a 2D SVC"""
    x = np.linspace(plt.xlim()[0], plt.xlim()[1], 30)
    y = np.linspace(plt.ylim()[0], plt.ylim()[1], 30)
    Y, X = np.meshgrid(y, x)
    P = np.zeros_like(X)
    for i, xi in enumerate(x):
        for j, yj in enumerate(y):
            P[i, j] = clf.decision_function([xi, yj])
    return plt.contour(X, Y, P, colors='k',
                       levels=[-1, 0, 1],
                       linestyles=['--', '-', '--'])

from sklearn.svm import SVC
classifier = SVC(kernel='linear')
classifier.fit(X, y)

plt.scatter(X[:, 0], X[:, 1], c=y, s=80)
plot_svc_decision_function(classifier)

# Plot the support vectors
plt.scatter(X[:, 0], X[:, 1], c=y, s=80)
plot_svc_decision_function(classifier)
plt.scatter(classifier.support_vectors_[:, 0], classifier.support_vectors_[:, 1],
            s=200, facecolors='none')

plt.show()
