import logging
import argparse
from pathlib import Path

from ruamel.yaml import YAMLError

from . import yaml
from .reader import DirReader, get_reader
from .models import decorate_object
from .writer import FileWriter, DirWriter
from .filter import registry as filters_registry

epilog = '''
OUTPUT can be one of:
  FILENAME
  file:FILENAME
  dir:DIRNAME
  dir:DIRNAME:by_namespace=false:by_api_group_kind=false

FILTER can be one of:
  remove_namespace
  remove_tiller_labels
  external:CMD:format=yaml/json
'''

output_types = {
    'file': FileWriter,
    'dir': DirWriter,
}


def main():
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, epilog=epilog)
    arg_parser.add_argument('--remove-namespace', action='store_true', help='remove namespace from objects')
    arg_parser.add_argument('--remove-tiller-labels', action='store_true', help='remove helm tiller labels')
    arg_parser.add_argument('--log-level', default='WARNING')
    arg_parser.add_argument('-f', '--filter', action='append', default=[], help='see below for formats')
    arg_parser.add_argument('inputs', metavar='INPUT', nargs='+', help='file or directory name')
    arg_parser.add_argument('output', metavar='OUTPUT', help='see below for formats')
    args = arg_parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=args.log_level)

    try:
        writer = parse_smart_arg(args.output, output_types, FileWriter)
    except (KeyError, TypeError, ValueError) as error:
        arg_parser.error(f'Invalid OUTPUT format: {error}')

    filters = []
    for spec in args.filter:
        try:
            filters.append(parse_smart_arg(spec, filters_registry))
        except (KeyError, TypeError, ValueError, OSError, YAMLError) as error:
            arg_parser.error(f'Invalid filter {spec!r}: {error}')

    def process_object(obj):
        obj = decorate_object(obj)
        for f in filters:
            obj = f.process(obj)
            if obj is None:
                return
        writer.write(obj)

    try:
        with writer.open():
            for input in args.inputs:
                reader = get_reader(input)
                if isinstance(reader, DirReader):
                    source = Path(reader.root).resolve()
                    destination = writer.path.resolve()
                    if destination.is_relative_to(source) or source.is_relative_to(destination):
                        raise ValueError('Directory inputs and outputs must not overlap')
                for obj in reader:
                    process_object(obj)
    except (OSError, ValueError, YAMLError) as error:
        arg_parser.exit(1, f'{arg_parser.prog}: {error}\n')


def parse_smart_arg(arg, class_map, default_class=None):
    parts = arg.split(':')
    if default_class and len(parts) == 1:
        return default_class(parts[0])
    class_name = parts[0]
    klass = class_map[class_name]
    if len(parts) > 1 and parts[1]:
        args = (parts[1],)
    else:
        args = ()
    if len(parts) > 2:
        kwargs = parse_smart_kwargs(parts[2:])
    else:
        kwargs = {}
    return klass(*args, **kwargs)


def parse_smart_kwargs(parts):
    kwargs = {}
    for part in parts:
        k, v = part.split('=', maxsplit=1)
        kwargs[k] = yaml.load(v)
    return kwargs


if __name__ == '__main__':
    main()
