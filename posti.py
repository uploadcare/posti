import os
from threading import Thread
from contextlib import contextmanager


__all__ = ['get_reader', 'iterator', 'lines_iterator']


class _ChattyFileWrapper(object):
    """Fd's returned by os.pipe() are not seakable and also don't support
    .tell() method while some APIs (like tarfile.open()) use it.
    """
    def __init__(self, silent_file):
        self._silent_file = silent_file
        self._position = 0

    def write(self, _s):
        # No kwargs are possible, only one positional argument
        self._position += len(_s)
        return self._silent_file.write(_s)

    def tell(self):
        return self._position

    def __getattr__(self, attr):
        return getattr(self._silent_file, attr)


class _HystericalFileWrapper(object):
    def __init__(self, calm_file):
        self._calm_file = calm_file
        self._exception = None

    def read(self, _n=-1):
        r = self._calm_file.read(_n)
        if self._exception is not None:
            raise self._exception
        return r

    def readline(self, _n=-1):
        r = self._calm_file.readline(_n)
        if self._exception is not None:
            raise self._exception
        return r

    def readlines(self, _h=-1):
        r = self._calm_file.readline(_h)
        if self._exception is not None:
            raise self._exception
        return r

    def __getattr__(self, attr):
        return getattr(self._calm_file, attr)


def run_writer(writer, wpipe, binary, set_exception):
    # File should always be closed after writing
    with os.fdopen(wpipe, 'wb' if binary else 'w') as wfile:
        try:
            writer(_ChattyFileWrapper(wfile))
        except Exception as e:
            set_exception(e)
            raise


@contextmanager
def get_reader(writer, binary=True, wait_writer=False):
    """Runs writer in another thread and returns context manager which
    exposes readable file.

    With wait_writer you MUST read the file to the end or raise exception.
    """
    rpipe, wpipe = os.pipe()
    rfile = os.fdopen(rpipe, 'rb' if binary else 'r')
    rfile = _HystericalFileWrapper(rfile)

    def set_ex(exception):
        rfile._exception = exception

    try:
        p = Thread(target=run_writer, args=(writer, wpipe, binary, set_ex))
        p.start()

        yield rfile
        
        if wait_writer:
            p.join()
    finally:
        rfile.close()


def iterator(writer, binary=True, chunk_size=32 * 1024):
    """Runs writer in another thread and returns iterator to 
    """
    # wait_writer because in all positive cases we read the file to the end
    with get_reader(writer, binary, wait_writer=True) as rfile:
        while True:
            r = rfile.read(chunk_size)
            if not r:
                break
            yield r


def lines_iterator(writer):
    # wait_writer because in all positive cases we read the file to the end
    with get_reader(writer, binary=False, wait_writer=True) as rfile:
        while True:
            r = rfile.readline()
            if not r:
                break
            yield r
