import io
import os

from .fs import StreamReader, DirReader


def get_reader(spec):
    if isinstance(spec, io.IOBase):
        return StreamReader(spec)
    elif not os.path.isdir(spec):
        with open(spec, 'rb') as fp:
            fp = io.BytesIO(fp.read())  # ruamel.yaml doesn't work well with streaming
            return StreamReader(fp)
    else:
        return DirReader(spec)
