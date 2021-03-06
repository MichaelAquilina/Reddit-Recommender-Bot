from __future__ import division, print_function

import numpy as np
from sklearn.svm import SVC


def get_strong_pos_features(X, y, threshold=1.0):
    # Generate a list of strong positive features for filtering
    strong_pos_features = np.zeros(X.shape[1])

    # TODO: Decide which one is better!
    # Binarize X
    A = np.zeros(X.shape)
    A[X > 0] = 1.0
    # Use X weights
    # A = X

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

    def __init__(self, **svm_args):
        self.classifier = None
        self.svm_args = svm_args
        self.iterations = 0
        self.pages = None  # TODO: REMOVE ME

    def __repr__(self):
        parameters = ['%s=%s' % pair for pair in self.svm_args.items()]
        return 'PEBL(%s)' % ', '.join(parameters)

    def predict(self, X):
        return self.classifier.predict(X)

    # Using sklearns interface, but it may mean jumping through some extra hoops
    def fit(self, X, y):
        strong_pos_features = get_strong_pos_features(X, y, threshold=1.0)

        P = []
        N = []

        P_index = []
        N_index = []

        index = np.arange(y.size)

        POS = X[y == 1]  # Positive set
        U = X[y == 0]  # Unlabelled set

        POS_index = index[y == 1]
        U_index = index[y == 0]

        initial_class = np.dot(U, strong_pos_features)
        P.append(U[initial_class > 0])
        N.append(U[initial_class == 0])

        P_index.append(U_index[initial_class > 0])
        N_index.append(U_index[initial_class == 0])

        i = 0
        NEG = N[0]
        while N[i].size > 0:
            self.classifier = SVC(**self.svm_args)

            XX = np.concatenate((POS, NEG))
            yy = np.zeros(XX.shape[0])
            yy[0:POS.shape[0]] = 1.0  # Create the label vector for this subspace

            self.classifier.fit(XX, yy)
            pred = self.classifier.predict(P[i])

            P.append(P[i][pred == 1.0])
            N.append(P[i][pred == 0.0])

            P_index.append(P_index[i][pred == 1.0])
            N_index.append(P_index[i][pred == 0.0])

            NEG = np.concatenate((NEG, N[i + 1]))
            i += 1

        self.iterations = i  # Store the number of iterations taken
