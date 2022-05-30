import os
from textwrap import dedent

from kube_manifest_processor import yaml


def load_file(name, bytes=False):
    path = os.path.join(os.path.dirname(__file__), name)
    with open(path, 'rb' if bytes else 'r') as fp:
        return fp.read()


def test_roundtrip():
    original = load_file('test1.yaml')
    assert yaml.dumps(yaml.load(original)) == original


def test_multiline():
    assert yaml.dumps({
        'key': 'line1\nline2\nline3\n',
    }) == dedent("""\
    key: |
      line1
      line2
      line3
    """)
