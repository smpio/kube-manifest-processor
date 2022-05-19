import os
import shutil

from .yaml import yaml


class FileWriter:
    def __init__(self, spec):
        if hasattr(spec, 'write'):
            self.fp = spec
        else:
            self.fp = open(spec, 'w')

    def write(self, obj):
        self.fp.write('---\n')
        self.fp.flush()
        yaml_dump(obj, self.fp)


class DirWriter:
    def __init__(self, path):
        self.root = path
        self.include_namespace = False
        shutil.rmtree(self.root, ignore_errors=True)

    def write(self, obj):
        group_version = obj['apiVersion']
        if group_version == 'v1':
            subpath = '_core'
        else:
            subpath, _ = group_version.split('/', maxsplit=1)

        kind = obj['kind']
        metadata = obj['metadata']
        name = metadata['name']
        namespace = metadata.get('namespace') or '_'

        if self.include_namespace:
            dir_path = os.path.join(self.root, namespace, subpath, kind)
        else:
            dir_path = os.path.join(self.root, subpath, kind)

        os.makedirs(dir_path, exist_ok=True)
        path = os.path.join(dir_path, name)

        with open(path + '.yaml', 'w') as fp:
            yaml_dump(obj, fp)


def yaml_dump(obj, fp):
    yaml.dump(obj, fp)
