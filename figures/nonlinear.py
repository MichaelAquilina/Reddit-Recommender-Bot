from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap
from sklearn.datasets import make_circles
from sklearn.svm import SVC

from figutils import plot_svc_decision_function

X, y = make_circles(n_samples=200, noise=0.11, random_state=0, factor=0.3)

classifier = SVC(kernel='rbf')
classifier.fit(X, y)

cm_bright = ListedColormap(['#FF0000', '#0000FF'])

plt.scatter(X[:, 0], X[:, 1], c=y, cmap=cm_bright, s=80)

plot_svc_decision_function(classifier, plt)

plt.gcf().canvas.set_window_title('nonlinear')

plt.tight_layout()
plt.show()
