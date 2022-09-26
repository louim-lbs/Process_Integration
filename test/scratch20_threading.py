import threading
import time

s_print_lock = threading.Lock()

def s_print(*a, **b):
    """Thread safe print function from: https://stackoverflow.com/questions/40356200/python-printing-in-multiple-threads"""
    s_print_lock.acquire()
    print(*a, **b)
    s_print_lock.release()

def func1():
    c.acquire()
    for i in range(100):
        print('i', i)
        c.notify_all()
        c.wait()
    c.notify_all()
    c.release()
    return 0

def func2():
    c.acquire()
    for i in range(100):
        print('j', i)
        c.notify_all()
        c.wait()
    return 0

c = threading.Condition()

t1 = threading.Thread(target=func1)
t2 = threading.Thread(target=func2)

t1.start()
t2.start()

t1.join()
t2.join()

exit()