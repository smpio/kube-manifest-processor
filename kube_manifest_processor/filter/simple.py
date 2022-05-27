import io
import json
import subprocess
import collections

from .base import Filter
from ..yaml import YAML
from ..models import GroupVersionKind


class RemoveNamespace(Filter, name='remove_namespace'):
    def process(self, obj):
        obj['metadata'].pop('namespace', None)
        return obj


class RemoveTillerLabels(Filter, name='remove_tiller_labels'):
    def process(self, obj):
        metadata = obj['metadata']
        label_maps = [
            metadata.get('labels'),
            obj.get('spec', {}).get('template', {}).get('metadata', {}).get('labels'),
            obj.get('spec', {}).get('selector', {}),
        ]
        for labels in label_maps:
            if labels:
                labels.pop('chart', None)
                labels.pop('release', None)
                labels.pop('heritage', None)
        return obj


class External(Filter, name='external'):
    def __init__(self, command, format='yaml'):
        self.command = command
        self.format = format

    def process(self, obj):
        if self.format == 'yaml':
            fp = io.BytesIO()
            YAML().dump(obj, fp)
            marshalled = fp.getvalue()
        elif self.format == 'json':
            marshalled = json.dumps(obj).encode()
        else:
            raise Exception(f'Invalid format: {self.format}')

        result = subprocess.run(self.command, shell=True, input=marshalled, capture_output=True, check=True)
        return YAML().load(result.stdout)


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


class DropServiceAccountTokens(Filter, name='drop_sa_tokens'):
    def process(self, obj):
        if obj._gvk != GroupVersionKind('', 'v1', 'Secret'):
            return obj
        if obj.get('type') == 'kubernetes.io/service-account-token':
            return None
        return obj


class DropDefaultServiceAccount(Filter, name='drop_default_sa'):
    def process(self, obj):
        if obj._gvk != GroupVersionKind('', 'v1', 'ServiceAccount'):
            return obj
        if obj.get('metadata', {}).get('name') == 'default':
            return None
        return obj


class DropKubeRootCA(Filter, name='drop_kube_root_ca'):
    def process(self, obj):
        if obj._gvk != GroupVersionKind('', 'v1', 'ConfigMap'):
            return obj
        if obj.get('metadata', {}).get('name') == 'kube-root-ca.crt':
            return None
        return obj


class DropSnapshots(Filter, name='drop_snapshots'):
    def process(self, obj):
        if obj._gvk.group == 'snapshot.storage.k8s.io' and obj._gvk.kind == 'VolumeSnapshot':
            return None
        return obj


class DropTLSSecrets(Filter, name='drop_tls_secrets'):
    def process(self, obj):
        if obj._gvk != GroupVersionKind('', 'v1', 'Secret'):
            return obj
        if obj.get('type') == 'kubernetes.io/tls':
            return None
        return obj


class DropDefaultNetworkPolicy(Filter, name='drop_default_network_policy'):
    def process(self, obj):
        if obj._gvk.group == 'networking.k8s.io' and obj._gvk.kind == 'NetworkPolicy':
            if obj.get('metadata', {}).get('name') == 'default':
                return None
        return obj


class DropAdminsRBAC(Filter, name='drop_admins_rbac'):
    def process(self, obj):
        if obj._gvk.group == 'rbac.authorization.k8s.io' and obj._gvk.kind == 'RoleBinding':
            if obj.get('metadata', {}).get('name') == 'admins':
                return None
        return obj


class Drop(Filter, name='drop'):
    def __init__(self, *, group=None, version=None, kind=None, name=None):
        self.group = group
        self.version = version
        self.kind = kind
        self.name = name

    def process(self, obj):
        if self.group is not None:
            if self.group != obj._gvk.group:
                return obj
        if self.version is not None:
            if self.version != obj._gvk.version:
                return obj
        if self.kind is not None:
            if self.kind != obj._gvk.kind:
                return obj
        if self.name is not None:
            if self.name != obj.get('metadata', {}).get('name'):
                return obj
        return None
