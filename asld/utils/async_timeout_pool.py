from time import time
from multiprocessing import Pool
from multiprocessing.context import TimeoutError as TLE
from signal import SIGINT, SIG_IGN, signal

from asld.utils.color_print import Color

class AsyncTimeOutPool:
    @classmethod
    def ignoreSIGINT(cls):
        signal(SIGINT, SIG_IGN)

    def __init__(self, pool_size, timeout=60):
        self.pool = Pool(pool_size, AsyncTimeOutPool.ignoreSIGINT)  # Workaround python mp-bug
        self.timeout = timeout

    def map(self, fun, requests):
        it = self.pool.imap_unordered(fun, requests)

        deadline = time() + self.timeout  # This shouldn't be needed :c
        while time() < deadline:
            try:
                yield it.next(self.timeout)
            except StopIteration:
                break
            except (TimeoutError, TLE):
                continue
            except Exception as e:
                Color.RED.print("\nA map result terminated on: (%s) %s" % (type(e), e))
                continue

    def close(self):
        self.pool.close()
