import io
import json
import subprocess

from .base import Filter
from ..yaml import yaml


class RemoveNamespace(Filter, name='remove_namespace'):
    def process(self, obj):
        obj['metadata'].pop('namespace', None)


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

        result = subprocess.run([self.command], input=marshalled, capture_output=True, check=True)
        return yaml.load(result.stdout)
