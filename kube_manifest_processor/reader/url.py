import requests
from ruamel.yaml.comments import CommentedMap

from ..yaml import YAML


class URLReader:
    def __init__(self, url):
        self.url = url

    def __iter__(self):
        resp = requests.get(self.url)
        resp.raise_for_status()
        ctype = resp.headers.get('content-type')
        if ctype == 'application/json':
            yield resp.json(object_pairs_hook=CommentedMap)
        else:
            yield from exclude_empty_documents(YAML().load_all(resp.text))


def exclude_empty_documents(docs):
    return (doc for doc in docs if doc is not None)
