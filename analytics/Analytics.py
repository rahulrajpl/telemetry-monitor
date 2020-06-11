"""
Analytics on time series based on the paper
'Truth Will Out: Departure-Based Process-Level Detection of
Stealthy Attacks on Control Systems'
Link:(https://dl.acm.org/doi/10.1145/3243734.3243781)'

"""
import pandas as pd
import numpy as np
from scipy.linalg import hankel, eigh


class ObluAnalytics:
    def __init__(self, lag_vector_length=50):
        self.lag_vector_length = lag_vector_length

    def get_threshold_score(self, data_path='../sensor/GetData/steps.txt'):
        df = pd.read_csv(data_path, skiprows=1, header=None, usecols=[1, 2])
        x_train_data = (df[1] + df[2]) / 2

        # N = len(x_train_data)
        L = self.lag_vector_length
        print(L)
        x_train = hankel(x_train_data[:L], x_train_data[L - 1:])  # Creating trajectory matrix
        eigen_values, eigen_vectors = eigh(np.matmul(x_train, x_train.T))
        idx = eigen_values.argsort()[::-1]
        # eigen_values = eigen_values[idx]
        eigen_vectors = eigen_vectors[:, idx]

        r = 1  # Statistical dimension decided as per scree plot
        U, sigma, V = np.linalg.svd(x_train)
        V = V.T
        x_elem = np.array([sigma[i] * np.outer(U[:, i], V[:, i]) for i in range(0, r)])
        x_train_extracted = x_elem.sum(axis=0)

        U = eigen_vectors[:, :r]
        UT = U.T
        pX = np.matmul(UT, x_train_extracted)
        centroid = np.mean(pX, axis=1)
        centroid = centroid[:, np.newaxis]

        # Calculating the departure threshold in signal subspace using centroid and UT

        xt = hankel(x_train_data[:L], x_train_data[L - 1:])
        pxt = np.matmul(UT, xt)
        dt_matrix = centroid - pxt
        dt_scores = np.linalg.norm(dt_matrix, axis=0, ord=2)
        theta = np.max(dt_scores)
        return UT, centroid, theta

    @staticmethod
    def get_score(UT, centroid, x, y):
        x, y = np.array(x, dtype='float64'), np.array(y, dtype='float64')
        stream = [np.sum(z) / 2 for z in list(zip(x, y))]
        stream = np.array(stream, dtype='float64')
        lag_vector = stream[:, np.newaxis]
        projected_lag_vector = np.matmul(UT, lag_vector)
        dist = centroid - projected_lag_vector
        score = np.linalg.norm(dist, ord=2)
        # print(score)
        return score
