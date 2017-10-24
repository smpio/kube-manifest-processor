import os
import shutil
from datetime import datetime

import yaml


class FileWriter:
    def __init__(self, spec):
        if hasattr(spec, 'write'):
            self.fp = spec
        else:
            self.fp = open(spec, 'w')

    def write(self, obj):
        self.fp.write('---\n')
        yaml_dump(obj, self.fp)


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
            yaml_dump(obj, fp)


def yaml_dump(obj, fp):
    yaml.dump(obj, stream=fp, Dumper=Dumper, default_flow_style=False)


class Dumper(yaml.SafeDumper):
    pass


def _datetime_representer(dumper, data):
    value = data.isoformat('T') + 'Z'
    return dumper.represent_scalar('tag:yaml.org,2002:timestamp', value)


Dumper.add_representer(datetime, _datetime_representer)
