import os
import shutil
import stat
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory, mkdtemp

from . import yaml


class FileWriter:
    def __init__(self, spec):
        self.path = Path(spec)

    @contextmanager
    def open(self):
        try:
            mode = self.path.stat().st_mode
        except FileNotFoundError:
            mode = None

        if mode is not None and not stat.S_ISREG(mode):
            # Devices and pipes are streams, so write to them directly.
            with self.path.open('w') as self.fp:
                yield
            return

        path = self.path.resolve()
        with TemporaryDirectory(prefix='.kmp-', dir=path.parent) as temp:
            staged = Path(temp) / 'output'
            with staged.open('w') as self.fp:
                yield
            if mode is not None:
                staged.chmod(stat.S_IMODE(mode))
            staged.replace(path)

    def write(self, obj):
        self.fp.write('---\n')
        self.fp.flush()
        yaml.dump(obj, self.fp)


class DirWriter:
    def __init__(self, path, by_namespace=True, by_api_group_kind=True):
        self.path = Path(os.path.abspath(path))
        self.by_namespace = by_namespace
        self.by_api_group_kind = by_api_group_kind

    @contextmanager
    def open(self):
        if not self.path.name or self.path.is_symlink() or (self.path.exists() and not self.path.is_dir()):
            raise ValueError(f'Expected a directory output path: {self.path}')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix='.kmp-', dir=self.path.parent) as temp:
            self.staged = Path(temp) / 'output'
            yield
            self.publish()

    def publish(self):
        if not self.path.exists():
            if self.staged.exists():
                self.staged.replace(self.path)
            return

        # Keep the previous tree available until the new tree is in place.
        backup = Path(mkdtemp(prefix='.kmp-backup-', dir=self.path.parent))
        previous = backup / 'previous'
        try:
            self.path.replace(previous)
        except OSError:
            backup.rmdir()
            raise
        try:
            if self.staged.exists():
                self.staged.replace(self.path)
        except (OSError, KeyboardInterrupt):
            try:
                if self.path.exists() or self.path.is_symlink():
                    raise FileExistsError(self.path)
                previous.replace(self.path)
            except OSError as error:
                raise OSError(f'Could not restore {self.path}; previous output is at {previous}') from error
            backup.rmdir()
            raise
        shutil.rmtree(backup)

    def write(self, obj):
        metadata = obj['metadata']
        parts = []

        if self.by_namespace:
            parts.append(metadata.get('namespace') or '_')

        if self.by_api_group_kind:
            parts.extend((obj._gvk.group or '_core', obj['kind']))

        parts.append(metadata['name'])
        if any(not isinstance(part, str) or part in ('', '.', '..') or Path(part).name != part for part in parts):
            raise ValueError(f'Invalid manifest output path components: {parts!r}')
        path = self.staged.joinpath(*parts[:-1], parts[-1] + '.yaml')
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open('w') as fp:
            yaml.dump(obj, fp)
