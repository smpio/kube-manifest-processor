import json
import subprocess

from .base import ObjectFilter, TextFilter
from ..yaml import yaml


class RemoveNamespace(ObjectFilter, name='remove_namespace'):
    def process(self, obj):
        obj['metadata'].pop('namespace', None)


class RemoveTillerLabels(ObjectFilter, name='remove_tiller_labels'):
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


class External(TextFilter, name='external'):
    def __init__(self, command, format='yaml'):
        self.command = command
        self.format = format

    def process(self, text):
        with subprocess.Popen(['kube-yaml-cleaner'], stdin=subprocess.PIPE, stdout=fp, encoding='utf-8') as proc:
            json.dump(obj, proc.stdin)
