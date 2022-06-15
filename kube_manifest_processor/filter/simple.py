import io
import re
import json
import fnmatch
import subprocess
import collections

from .base import Filter
from ..models import GroupVersionKind
from .. import yaml


class RemoveNamespace(Filter, name='remove_namespace'):
    def process(self, obj):
        obj['metadata'].pop('namespace', None)
        return obj


class External(Filter, name='external'):
    def __init__(self, command, format='yaml'):
        self.command = command
        self.format = format

    def process(self, obj):
        if self.format == 'yaml':
            fp = io.BytesIO()
            yaml.dump(obj, fp)
            marshalled = fp.getvalue()
        elif self.format == 'json':
            marshalled = json.dumps(obj).encode()
        else:
            raise Exception(f'Invalid format: {self.format}')

        result = subprocess.run(self.command, shell=True, input=marshalled, capture_output=True, check=True)
        return yaml.load(result.stdout)


class RemovePrefix(Filter, name='remove_prefix'):
    def __init__(self, prefix):
        self.prefix = prefix

    def process(self, obj):
        if isinstance(obj, collections.MutableMapping):
            for k, v in obj.items():
                if k == 'name' and isinstance(v, str):
                    obj[k] = obj[k].removeprefix(self.prefix)
                else:
                    self.process(v)
        elif isinstance(obj, list):
            for v in obj:
                self.process(v)
        return obj


class Drop(Filter, name='drop'):
    def __init__(self, group_kind, **filters):
        group_glob, kind_glob = group_kind.split('/')
        self.group_re = re.compile(fnmatch.translate(group_glob))
        self.kind_re = re.compile(fnmatch.translate(kind_glob))
        self.filters = {tuple(k.split('/')): yaml.load(v) for k, v in filters.items()}

    def process(self, obj):
        if not self.group_re.match(obj._gvk.group):
            return obj
        if not self.kind_re.match(obj._gvk.kind):
            return obj
        for k, v in self.filters.items():
            subdata = obj
            for kpart in k:
                if subdata is None:
                    return obj
                subdata = subdata.get(kpart)
            if subdata != v:
                return obj
        return None


class Remove(Filter, name='remove'):
    def __init__(self, group_kind, *, path):
        group_glob, kind_glob = group_kind.split('/')
        self.group_re = re.compile(fnmatch.translate(group_glob))
        self.kind_re = re.compile(fnmatch.translate(kind_glob))
        self.path = path.split('/')

    def process(self, obj):
        if not self.group_re.match(obj._gvk.group):
            return obj
        if not self.kind_re.match(obj._gvk.kind):
            return obj
        subobj = obj
        for path_part in self.path[:-1]:
            if not isinstance(subobj, dict):
                return obj
            subobj = subobj.get(path_part)
            if not subobj:
                return obj
        last_part = self.path[-1]
        subobj.pop(last_part, None)
        return obj


class CleanPVC(Filter, name='clean_pvc'):
    def process(self, obj):
        if obj._gvk != GroupVersionKind('', 'v1', 'PersistentVolumeClaim'):
            return obj
        anns = obj.get('metadata', {}).get('annotations', {})
        anns.pop('pv.kubernetes.io/bind-completed', None)
        anns.pop('pv.kubernetes.io/bound-by-controller', None)
        anns.pop('volume.beta.kubernetes.io/storage-provisioner', None)
        anns.pop('volume.kubernetes.io/selected-node', None)
        anns.pop('volume.kubernetes.io/storage-resizer', None)
        spec = obj.get('spec', {})
        spec.pop('volumeName', None)
        return obj


class CleanService(Filter, name='clean_service'):
    def process(self, obj):
        if obj._gvk != GroupVersionKind('', 'v1', 'Service'):
            return obj
        spec = obj.get('spec', {})
        spec.pop('clusterIP', None)
        spec.pop('clusterIPs', None)
        spec.pop('healthCheckNodePort', None)
        for port in spec.get('ports', []):
            port.pop('nodePort', None)
        return obj


class DropOwned(Filter, name='drop_owned'):
    def process(self, obj):
        if 'ownerReferences' in obj.get('metadata', {}):
            return None
        return obj
