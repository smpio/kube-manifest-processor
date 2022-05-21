import io
import os

from .yaml import YAML


def get_reader(spec):
    if isinstance(spec, io.IOBase):
        return StreamReader(spec)
    elif not os.path.isdir(spec):
        with open(spec, 'rb') as fp:
            fp = io.BytesIO(fp.read())  # ruamel.yaml doesn't work well with streaming
            return StreamReader(fp)
    else:
        return DirReader(spec)


class DirReader:
    def __init__(self, path):
        self.root = path

    def __iter__(self):
        for root, dirs, files in os.walk(self.root, followlinks=True, onerror=reraise):
            for file in files:
                path = os.path.join(root, file)
                with open(path, 'r') as fp:
                    yield from read_fp(fp)


class StreamReader:
    def __init__(self, spec):
        self.spec = spec

    def __iter__(self):
        return read_fp(self.spec)


def read_fp(fp):
    return exclude_empty_documents(YAML().load_all(fp))


def exclude_empty_documents(docs):
    return (doc for doc in docs if doc is not None)


def reraise(err):
    raise err
