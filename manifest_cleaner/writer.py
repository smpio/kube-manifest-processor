import os
import shutil

import yaml


class FileWriter:
    def __init__(self, spec):
        if hasattr(spec, 'write'):
            self.fp = spec
        else:
            self.fp = open(spec, 'w')

    def write(self, obj):
        self.fp.write('---\n')
        yaml.safe_dump(obj, default_flow_style=False, stream=self.fp)


class DirWriter:
    def __init__(self, path):
        self.root = path
        self.include_namespace = False
        shutil.rmtree(self.root, ignore_errors=True)

    def write(self, obj):
        kind = obj['kind']
        metadata = obj['metadata']
        name = metadata['name']
        namespace = metadata.get('namespace') or '_'

        if self.include_namespace:
            dir_path = os.path.join(self.root, namespace, kind)
        else:
            dir_path = os.path.join(self.root, kind)

        os.makedirs(dir_path, exist_ok=True)
        path = os.path.join(dir_path, name)

        with open(path + '.yaml', 'w') as fp:
            yaml.safe_dump(obj, default_flow_style=False, stream=fp)
