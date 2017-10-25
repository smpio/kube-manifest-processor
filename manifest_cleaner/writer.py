import os
import json
import shutil
import subprocess


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
    with subprocess.Popen(['kube-yaml-cleaner'], stdin=subprocess.PIPE, stdout=fp, encoding='utf-8') as proc:
        json.dump(obj, proc.stdin)
