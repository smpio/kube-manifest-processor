import os
import shutil

from . import yaml


class FileWriter:
    def __init__(self, spec):
        self.fp = open(spec, 'w')

    def write(self, obj):
        self.fp.write('---\n')
        self.fp.flush()
        yaml.dump(obj, self.fp)


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
            dir_path = os.path.join(dir_path, obj._gvk.group or '_core', obj['kind'])

        os.makedirs(dir_path, exist_ok=True)
        path = os.path.join(dir_path, name)

        with open(path + '.yaml', 'w') as fp:
            yaml.dump(obj, fp)
