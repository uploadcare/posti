from __future__ import unicode_literals

import os
import sys
from time import sleep
from unittest import TestCase
from contextlib import contextmanager

from .posti import get_reader, iterator, lines_iterator


@contextmanager
def stdchannel_redirected(stdchannel, dest_filename):
    """A context manager to temporarily redirect stdout or stderr
    """
    try:
        oldstdchannel = os.dup(stdchannel.fileno())
        dest_file = open(dest_filename, 'w')
        os.dup2(dest_file.fileno(), stdchannel.fileno())
        yield
    finally:
        if oldstdchannel is not None:
            os.dup2(oldstdchannel, stdchannel.fileno())
        if dest_file is not None:
            dest_file.close()


class TestGetReader(TestCase):
    def test_dummy_writer(self):
        def writer(wfile):
            pass

        with get_reader(writer) as rfile:
            self.assertEquals(rfile.read(), b'')

    def test_tiny_writer(self):
        def writer(wfile):
            wfile.write(b'test')

        with get_reader(writer) as rfile:
            self.assertEquals(rfile.read(), b'test')

    def test_wait_writer(self):
        def writer(wfile):
            wfile.write(b'test')

        with get_reader(writer, wait_writer=True) as rfile:
            self.assertEquals(rfile.read(), b'test')

    def test_massive_writer(self):
        def writer(wfile):
            payload = b'1234567890' * 1024  # 10k
            for _ in range(1024):
                wfile.write(payload)

        with get_reader(writer) as rfile:
            l = 0
            r = True
            while r:
                r = rfile.read(32 * 1024)
                l += len(r)
            self.assertEquals(l, 10 * 1024 * 1024)

    def test_incomplete_read(self):
        state = {
            'finnished': False,
            'interrupted': True,
        }
        def writer(wfile):
            payload = b'1234567890' * 1024  # 10k
            try:
                for _ in range(1024):
                    wfile.write(payload)
                state['interrupted'] = False
            finally:
                state['finnished'] = True

        with stdchannel_redirected(sys.stderr, os.devnull):
            with get_reader(writer) as rfile:
                self.assertEquals(rfile.read(10), b'1234567890')
                self.assertEquals(state['finnished'], False)
                self.assertEquals(state['interrupted'], True)
            # Release GIL for a moment to resume the second thread
            sleep(0.02)
            self.assertEquals(state['finnished'], True)
            self.assertEquals(state['interrupted'], True)

    def test_exception_in_writer(self):
        def writer(wfile):
            wfile.write(b'test')
            raise ValueError()

        with stdchannel_redirected(sys.stderr, os.devnull):
            with get_reader(writer) as rfile:
                with self.assertRaises(ValueError):
                    rfile.read(10)
            # Wait until second thread print exception
            sleep(0.02)

    def test_text_mode(self):
        def writer(wfile):
            wfile.write('test')

        with get_reader(writer, binary=False) as rfile:
            self.assertEquals(rfile.read(), 'test')


class TestIterator(TestCase):
    def test_dummy_writer(self):
        def writer(wfile):
            pass

        for chunk in iterator(writer):
            self.assertFalse(True)

    def test_tiny_writer(self):
        def writer(wfile):
            wfile.write(b'test')

        for chunk in iterator(writer):
            self.assertEquals(chunk, b'test')

    def test_massive_writer(self):
        def writer(wfile):
            payload = b'1234567890' * 1024  # 10k
            for _ in range(1024):
                wfile.write(payload)

        l = 0
        for chunk in iterator(writer, chunk_size=2560):
            self.assertTrue(chunk.startswith(b'1234567890'))
            l += len(chunk)
        self.assertEquals(l, 10 * 1024 * 1024)

    def test_incomplete_read(self):
        state = {
            'finnished': False,
            'interrupted': True,
        }
        def writer(wfile):
            payload = b'1234567890' * 1024  # 10k
            try:
                for _ in range(1024):
                    wfile.write(payload)
                state['interrupted'] = False
            finally:
                state['finnished'] = True

        with stdchannel_redirected(sys.stderr, os.devnull):
            i = iterator(writer)
            self.assertTrue(next(i).startswith(b'1234567890'))
            self.assertEquals(state['finnished'], False)
            self.assertEquals(state['interrupted'], True)
            i.close()
            # Release GIL for a moment to resume the second thread
            sleep(0.02)
            self.assertEquals(state['finnished'], True)
            self.assertEquals(state['interrupted'], True)

    def test_exception_in_writer(self):
        def writer(wfile):
            wfile.write(b'test')
            raise ValueError()

        with stdchannel_redirected(sys.stderr, os.devnull):
            with self.assertRaises(ValueError):
                for chunk in iterator(writer, chunk_size=2):
                    self.assertFalse(True)
            # Wait until second thread print exception
            sleep(0.02)

    def test_text_mode(self):
        def writer(wfile):
            wfile.write('test')

        for chunk in iterator(writer, binary=False):
            self.assertEquals(chunk, 'test')

class TestLinesIterator(TestCase):
    def test_text_mode(self):
        def writer(wfile):
            wfile.write('test\n')
            wfile.write('test\n')
            wfile.write('test\n')
            wfile.write('test\n')

        for chunk in lines_iterator(writer):
            self.assertEquals(chunk, 'test\n')
