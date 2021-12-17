from multiprocessing import Pool
import time


def some_function(datum):
    # and returns the datum raised to the power of itself
    return datum**datum

def parallel_task(f, d):
    t = time.time()

    pool = Pool()
    results = pool.map(f, d)
    pool.close()
    pool.join()

    print(time.time()-t)

if __name__ == '__main__':
    data = range(10000)
    results = [] 

    t = time.time()

    for datum in data:
        results.append(some_function(datum))

    print(time.time()-t)
    

    parallel_task(some_function, data)
