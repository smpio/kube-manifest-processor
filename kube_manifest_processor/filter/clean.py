import re
import json
import logging

from .base import Filter
from ..models import GroupVersionKind

log = logging.getLogger(__name__)
readonly_re = re.compile(r'read[ -]only', re.I)
default_re = re.compile(r'defaults?\s+(?:to|\w+\s+is)\s+[\'"`]?([^"\'`\s\.\,\(]+)[\'"`]?[\,\.\s\(]', re.I)
true_re = re.compile(r'true|yes|1', re.I)
ref_prefix = '#/definitions/'


class Clean(Filter, name='clean'):
    def __init__(self, openapi_schema, *, drop_labels='', drop_annotations=''):
        # kubectl get --raw /openapi/v2
        with open(openapi_schema, 'rb') as fp:
            self.schema = decorate_schema(json.load(fp))

        self.gvk_map = {}
        for d in self.schema['definitions'].values():
            gvks = d.get('x-kubernetes-group-version-kind', [])
            for gvk_dict in gvks:
                gvk = GroupVersionKind(**gvk_dict)
                self.gvk_map[gvk] = d

        self.drop_labels = drop_labels.split(',') + [
            'controller-uid',
            'job-name',
            'pod-template-hash',
        ]

        self.drop_annotations = drop_annotations.split(',') + [
            'cni.projectcalico.org/containerID',
            'cni.projectcalico.org/podIP',
            'cni.projectcalico.org/podIPs',
            'kubernetes.io/psp',
            'kubectl.kubernetes.io/last-applied-configuration',
            'deployment.kubernetes.io/revision',
        ]

    def process(self, obj):
        d = self.gvk_map.get(obj._gvk)
        if not d:
            log.warning('No OpenAPI definition for %s', obj._gvk)
            return obj
        self._clean(obj, d)
        return obj

    def _clean(self, obj, d):
        if 'default' in d and obj == d['default']:
            raise _Drop()

        if '$ref' in d:
            ref = d['$ref']
            if ref == 'io.k8s.apimachinery.pkg.apis.meta.v1.ObjectMeta':
                if 'labels' in obj:
                    self.clean_labels(obj['labels'])
                if 'annotations' in obj:
                    self.clean_annotations(obj['annotations'])
            if ref == 'io.k8s.apimachinery.pkg.apis.meta.v1.LabelSelector':
                if 'matchLabels' in obj:
                    self.clean_labels(obj['matchLabels'])
            d = self.schema['definitions'].get(ref)
            if not d:
                return
            if 'default' in d and obj == d['default']:
                raise _Drop()

        if isinstance(obj, list) and 'items' in d:
            for item in obj:
                self._clean(item, d['items'])

        if isinstance(obj, dict) and 'properties' in d:
            for k, v in list(obj.items()):
                subdef = d['properties'].get(k)
                if not subdef:
                    continue
                try:
                    if subdef['read_only'] and k != 'readOnly':
                        raise _Drop()
                    self._clean(v, subdef)
                    if v == {} and k not in d.get('required', ()):
                        raise _Drop()
                except _Drop:
                    del obj[k]

    def clean_labels(self, labels):
        for label in self.drop_labels:
            labels.pop(label, None)

    def clean_annotations(self, annotations):
        for annotation in self.drop_annotations:
            annotations.pop(annotation, None)


def decorate_schema(schema):
    for d in schema['definitions'].values():
        decorate_definition(d)
        if 'x-kubernetes-group-version-kind' in d:
            d.get('properties', {}).get('status', {})['read_only'] = True

    # TODO: does not work!
    schema['definitions']['io.k8s.api.apps.v1.DeploymentStrategy']['default'] = {
        'type': 'RollingUpdate',
        'rollingUpdate': {
            'maxSurge': '25%',
            'maxUnavailable': '25%',
        },
    }

    schema['definitions']['io.k8s.api.apps.v1.DaemonSetUpdateStrategy']['default'] = {
        'type': 'RollingUpdate',
        'rollingUpdate': {
            'maxUnavailable': 1,
        },
    }

    schema['definitions']['io.k8s.api.apps.v1.StatefulSetUpdateStrategy']['default'] = {
        'type': 'RollingUpdate',
        'rollingUpdate': {
            'partition': 0,
        },
    }

    meta_props = schema['definitions']['io.k8s.apimachinery.pkg.apis.meta.v1.ObjectMeta']['properties']
    meta_props['finalizers']['read_only'] = True
    meta_props['ownerReferences']['read_only'] = True
    meta_props['generateName']['read_only'] = True
    meta_props['managedFields']['read_only'] = True

    pod_spec_props = schema['definitions']['io.k8s.api.core.v1.PodSpec']['properties']
    pod_spec_props['serviceAccount']['read_only'] = True  # deprecated
    pod_spec_props['schedulerName']['default'] = 'default-scheduler'

    schema['definitions']['io.k8s.api.core.v1.PodSecurityContext']['default'] = {}
    schema['definitions']['io.k8s.api.core.v1.ResourceRequirements']['default'] = {}

    return schema


def decorate_definition(d):
    if 'description' in d:
        d['read_only'] = bool(readonly_re.search(d['description']))
    else:
        d['read_only'] = False

    if '$ref' in d:
        d['$ref'] = d['$ref'].removeprefix(ref_prefix)
    elif 'properties' in d:
        for pd in d['properties'].values():
            decorate_definition(pd)
    elif d.get('type') == 'array':
        decorate_definition(d['items'])
    elif d.get('type') == 'object':
        d['properties'] = {}
    elif 'description' in d:
        m = default_re.search(d['description'])
        if m:
            d['default'] = m.group(1)
            if 'type' in d:
                if d['type'] == 'boolean':
                    d['default'] = bool(true_re.match(d['default']))
                elif d['type'] == 'integer':
                    if d['default'] == 'nil':
                        d['default'] = None
                    else:
                        d['default'] = d['default'].removesuffix('s')  # remove seconds suffix
                        try:
                            d['default'] = int(d['default'])
                        except ValueError:
                            del d['default']
                elif d['type'] == 'number':
                    d['default'] = float(d['default'])


class _Drop(Exception):
    pass
