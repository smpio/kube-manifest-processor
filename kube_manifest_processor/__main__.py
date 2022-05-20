import logging
import argparse

from .yaml import YAML
from .reader import get_reader
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
    arg_parser.add_argument('-f', '--filter', metavar='FILTER', nargs='*', help='see below for formats')
    arg_parser.add_argument('inputs', metavar='INPUT', nargs='+', help='file or directory name')
    arg_parser.add_argument('output', metavar='OUTPUT', help='see below for formats')
    args = arg_parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=args.log_level)

    try:
        writer = parse_smart_arg(args.output, output_types, FileWriter)
    except Exception:
        return arg_parser.error('Invalid OUTPUT format')

    if args.filter:
        try:
            filters = [parse_smart_arg(f, filters_registry) for f in args.filter]
        except Exception:
            return arg_parser.error('Invalid FILTER format')
    else:
        filters = []

    for input in args.inputs:
        reader = get_reader(input)
        for obj in reader:
            for f in filters:
                obj = f.process(obj)
            writer.write(obj)


def parse_smart_arg(arg, class_map, default_class=None):
    parts = arg.split(':')
    if default_class and len(parts) == 1:
        return default_class(parts[0])
    class_name = parts[0]
    klass = class_map[class_name]
    if len(parts) > 1:
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
        kwargs[k] = YAML().load(v)
    return kwargs


if __name__ == '__main__':
    main()
