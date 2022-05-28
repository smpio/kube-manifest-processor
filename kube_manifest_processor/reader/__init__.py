import io
import os
import urllib.parse

from .fs import StreamReader, DirReader
from .apiserver import ApiServerReader
from .url import URLReader


def get_reader(spec):
    if isinstance(spec, io.IOBase):
        return StreamReader(spec)
    else:
        parts = urllib.parse.urlparse(spec)
        if not parts.scheme or parts.scheme == 'file':
            spec = parts.path
            if not os.path.isdir(spec):
                with open(spec, 'rb') as fp:
                    fp = io.BytesIO(fp.read())  # ruamel.yaml doesn't work well with streaming
                    return StreamReader(fp)
            else:
                return DirReader(spec)
        elif parts.scheme in ('http', 'https') and parts.path in ('/', ''):
            return ApiServerReader(spec)
        else:
            return URLReader(spec)
