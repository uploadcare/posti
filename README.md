# posti

Posti (Finnish, posti — mail) — when you need to read what others can only write.

Some Python interfaces are able to write in files or file objects.
But what if you don't need to store the output to the file?
You could use `io.BytesIO` to store the output in the memory.
The drawback is that now all the data stored in the memory.

Posti provides the writer with a writeable append-only file
and convenient interface for the reader.

# Examples

Read tar file:

```python
import tarfile
import posti

def writer(wfile):
    with tarfile.open(mode='w', fileobj=wfile) as tar:
        tar.add('.')

l = 0
for chunk in posti.iterator(writer):
    l += len(chunk)
print("Tar length:", l)
```

All exceptions in the writer are propagated to the main thread:

```python
import posti

def writer(wfile):
    wfile.write(b'unreachable')
    raise ValueError('whoops')

for chunk in posti.iterator(writer):
    print(chunk)
```

```
Traceback (most recent call last):
  File "./ex.py", line 7, in <module>
    for chunk in posti.iterator(writer):
  : 5 non-project frames are hidden
  File "./ex.py", line 5, in writer
    raise ValueError('whoops')
ValueError: whoops
```

There is also `get_reader` context manager for low-level reading:

```python
import posti

def writer(wfile):
    wfile.write(b'test123')

with posti.get_reader(writer) as rfile:
    # prints only "test"
    print(rfile.read(4).decode())
```
