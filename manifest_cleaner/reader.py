import os

import yaml


def get_path_reader(path):
    if os.path.isdir(path):
        return DirReader(path)
    else:
        return FileReader(path)


class DirReader:
    def __init__(self, path):
        self.root = path

    def __iter__(self):
        for root, dirs, files in os.walk(self.root, followlinks=True, onerror=reraise):
            for file in files:
                path = os.path.join(root, file)
                yield from read_file(path)


class FileReader:
    def __init__(self, spec):
        self.spec = spec

    def __iter__(self):
        yield from read_file(self.spec)


def read_file(spec):
    if hasattr(spec, 'read'):
        fp = spec
    else:
        fp = open(spec, 'r')
    return yaml.load_all(fp, Loader=Loader)


def reraise(err):
    raise err


class Loader(yaml.SafeLoader):
    pass


Loader.yaml_constructors['tag:yaml.org,2002:timestamp'] = Loader.yaml_constructors['tag:yaml.org,2002:str']
