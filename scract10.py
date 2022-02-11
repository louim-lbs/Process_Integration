from math import sqrt
from joblib import Parallel, delayed
import time

t = time.time()
a = Parallel(n_jobs=2)(delayed(sqrt)(i ** 2) for i in range(10))
print(t - time.time())

t = time.time()
a = [sqrt(i ** 2) for i in range(10)]
print(t - time.time())

print(a)