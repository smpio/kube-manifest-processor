import os
import shutil

from .yaml import yaml


class FileWriter:
    def __init__(self, spec):
        self.fp = open(spec, 'w')

    def write(self, obj):
        self.fp.write('---\n')
        self.fp.flush()
        yaml_dump(obj, self.fp)


class DirWriter:
    def __init__(self, path, by_namespace=True, by_api_group_kind=True):
        self.root = path
        self.by_namespace = by_namespace
        self.by_api_group_kind = by_api_group_kind
        shutil.rmtree(self.root, ignore_errors=True)

    def write(self, obj):
        metadata = obj['metadata']
        name = metadata['name']

        dir_path = self.root

        if self.by_namespace:
            dir_path = os.path.join(dir_path, metadata.get('namespace') or '_')

        if self.by_api_group_kind:
            group_version = obj['apiVersion']
            if group_version == 'v1':
                api_group = '_core'
            else:
                api_group, _ = group_version.split('/', maxsplit=1)
            dir_path = os.path.join(dir_path, api_group, obj['kind'])

        os.makedirs(dir_path, exist_ok=True)
        path = os.path.join(dir_path, name)

        with open(path + '.yaml', 'w') as fp:
            yaml_dump(obj, fp)


def yaml_dump(obj, fp):
    yaml.dump(obj, fp)
