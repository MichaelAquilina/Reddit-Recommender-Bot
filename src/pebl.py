from __future__ import division, print_function

import numpy as np
from sklearn.svm import SVC


def get_strong_pos_features(X, y, threshold=1.0):
    # Generate a list of strong positive features for filtering
    strong_pos_features = np.zeros(X.shape[1])

    # TODO: Decide which one is better!
    # Binarize X
    # A = np.zeros(X.shape)
    # A[X > 0] = 1.0
    # Use X weights
    A = X

    pos_features = np.sum(A[y == 1, :], axis=0)
    unl_features = np.clip(np.sum(A[y == 0, :], axis=0), 1.0, np.inf)  # Prevent divide by 0s

    for i in xrange(pos_features.size):
        if pos_features[i] / unl_features[i] > threshold:
            strong_pos_features[i] = 1.0

    return strong_pos_features


class PEBL(object):
    """
    Positive Example Based Learning (PEBL) Framework for handling
    data sets with positive and unlabelled data. Unlabelled data
    constitutes a set of unknown labels which could either be
    positive or negative.
    """

    def __init__(self, C=1.0):
        self.classifier = None
        self.C = C  # Complexity Parameter

    def __repr__(self):
        return 'PEBL(C=%0.1f)' % (self.C, )

    def predict(self, X):
        return self.classifier.predict(X)

    # Using sklearns interface, but it may mean jumping through some extra hoops
    def fit(self, X, y):
        strong_pos_features = get_strong_pos_features(X, y, threshold=2.0)

        P = []
        N = []

        POS = X[y == 1, :]  # Positive set
        U = X[y == 0, :]  # Unlabelled set

        initial_class = np.dot(U, strong_pos_features)
        P.append(U[initial_class > 0])
        N.append(U[initial_class == 0])

        i = 0
        NEG = N[0]
        while N[i].size > 0:
            self.classifier = SVC(C=self.C, kernel='linear')

            XX = np.concatenate((POS, NEG))
            yy = np.zeros(XX.shape[0])
            yy[0:POS.shape[0]] = 1.0  # Create the label vector for this subspace

            self.classifier.fit(XX, yy)
            pred = self.classifier.predict(P[i])

            P.append(P[i][pred == 1.0])
            N.append(P[i][pred == 0.0])

            NEG = np.concatenate((NEG, N[i + 1]))
            i += 1
