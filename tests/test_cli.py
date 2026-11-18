import subprocess
import sys

from kube_manifest_processor import yaml


def test_filter_bundle_into_namespace_directories(tmp_path):
    bundle = tmp_path / 'bundle.yaml'
    bundle.write_text(
        'apiVersion: v1\n'
        'kind: Namespace\n'
        'metadata: {name: demo}\n'
        '---\n'
        'apiVersion: v1\n'
        'kind: ConfigMap\n'
        'metadata:\n'
        '  name: example\n'
        '  namespace: demo\n'
        '  labels:\n'
        '    app.kubernetes.io/managed-by: Helm\n'
        '    keep: example\n',
        encoding='utf-8',
    )
    output = tmp_path / 'output'

    subprocess.run(
        [
            sys.executable, '-m', 'kube_manifest_processor',
            '-f', 'drop:/Namespace',
            '-f', r'remove:*/*:path=metadata/labels/app.kubernetes.io\/managed-by',
            '--', str(bundle), f'dir:{output}',
        ],
        check=True,
    )

    expected = output / 'demo' / '_core' / 'ConfigMap' / 'example.yaml'
    assert list(output.rglob('*.yaml')) == [expected]
    manifest = yaml.load(expected.read_text(encoding='utf-8'))
    assert manifest['metadata']['labels'] == {'keep': 'example'}
