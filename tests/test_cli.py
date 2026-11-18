import subprocess
import sys
from pathlib import Path

import pytest

from kube_manifest_processor import yaml
from kube_manifest_processor.writer import DirWriter


def run_cli(*args):
    return subprocess.run(
        [sys.executable, '-m', 'kube_manifest_processor', *args],
        text=True,
        capture_output=True,
    )


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


@pytest.mark.parametrize('directory_output', [False, True], ids=['file', 'directory'])
@pytest.mark.parametrize('failure', ['invalid-filter', 'bad-second-input'])
def test_failure_preserves_existing_output(tmp_path, directory_output, failure):
    manifest = tmp_path / 'manifest.yaml'
    manifest.write_text('apiVersion: v1\nkind: ConfigMap\nmetadata: {name: new}\n')
    output = tmp_path / 'output'
    if directory_output:
        output.mkdir()
        previous = output / 'previous.yaml'
        destination = f'dir:{output}'
    else:
        previous = output
        destination = str(output)
    previous.write_text('previous output\n')

    if failure == 'invalid-filter':
        result = run_cli('-f', 'unknown', '--', str(manifest), destination)
        assert 'Invalid filter' in result.stderr
    else:
        bad = tmp_path / 'invalid.yaml'
        bad.write_text('[unclosed')
        result = run_cli('--', str(manifest), str(bad), destination)

    assert result.returncode != 0
    assert previous.read_text() == 'previous output\n'
    if directory_output:
        assert list(output.iterdir()) == [previous]
    assert not list(tmp_path.glob('.kmp-*'))


def test_replace_existing_directory_and_remove_it_when_empty(tmp_path):
    manifest = tmp_path / 'manifest.yaml'
    manifest.write_text('apiVersion: v1\nkind: ConfigMap\nmetadata: {name: example}\n')
    output = tmp_path / 'output'
    output.mkdir()
    previous = output / 'previous.yaml'
    previous.touch()

    result = run_cli('--', str(manifest), f'dir:{output}')
    assert result.returncode == 0, result.stderr
    assert not previous.exists()
    assert (output / '_' / '_core' / 'ConfigMap' / 'example.yaml').is_file()

    result = run_cli('-f', 'drop:/ConfigMap', '--', str(manifest), f'dir:{output}')
    assert result.returncode == 0, result.stderr
    assert not output.exists()
    assert not list(tmp_path.glob('.kmp-*'))


def test_failed_directory_publish_restores_previous_output(tmp_path, monkeypatch):
    output = tmp_path / 'output'
    output.mkdir()
    previous = output / 'previous.yaml'
    previous.write_text('previous output\n')
    writer = DirWriter(output)
    replace = Path.replace

    def fail_install(source, destination):
        if destination == output and source == writer.staged:
            raise OSError('could not install new tree')
        return replace(source, destination)

    monkeypatch.setattr(Path, 'replace', fail_install)
    with pytest.raises(OSError, match='could not install new tree'):
        with writer.open():
            writer.staged.mkdir()
    assert previous.read_text() == 'previous output\n'
    assert not list(tmp_path.glob('.kmp-*'))


def test_drop_distinguishes_yaml_values_and_remove_prefix_processes_nested_names(tmp_path):
    manifest = tmp_path / 'manifest.yaml'
    manifest.write_text(
        'apiVersion: apps/v1\nkind: Deployment\nmetadata: {name: prefix-number}\nspec: {replicas: 2}\n'
        '---\n'
        'apiVersion: apps/v1\nkind: Deployment\nmetadata: {name: prefix-string}\nspec: {replicas: "2"}\n'
        '---\n'
        'apiVersion: v1\nkind: List\nmetadata: {name: prefix-parent}\nitems: [{name: prefix-child}]\n'
    )
    output = tmp_path / 'output.yaml'
    result = run_cli(
        '-f', 'drop:apps/Deployment:spec/replicas=2',
        '-f', 'remove_prefix:prefix-',
        '--', str(manifest), str(output),
    )

    assert result.returncode == 0, result.stderr
    deployment, parent = yaml.load_all(output.read_text())
    assert deployment['metadata']['name'] == 'string'
    assert deployment['spec']['replicas'] == '2'
    assert parent['metadata']['name'] == 'parent'
    assert parent['items'] == [{'name': 'child'}]


@pytest.mark.parametrize(('value', 'kind'), [('[item]', 'a sequence'), ('text', 'a scalar')])
def test_remove_reports_unsupported_parent_type(tmp_path, value, kind):
    manifest = tmp_path / 'manifest.yaml'
    manifest.write_text(f'apiVersion: v1\nkind: ConfigMap\nmetadata: {{name: example}}\ndata: {value}\n')
    output = tmp_path / 'output.yaml'
    result = run_cli('-f', 'remove:/ConfigMap:path=data/0', '--', str(manifest), str(output))
    assert result.returncode != 0
    assert f"Remove path 'data/0' requires mapping keys (found {kind})" in result.stderr
    assert not output.exists()
