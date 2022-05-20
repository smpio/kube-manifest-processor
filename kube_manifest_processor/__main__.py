import sys
import logging
import argparse

from .yaml import yaml
from .reader import get_reader
from .cleaner import Cleaner
from .writer import FileWriter, DirWriter

output_arg_help = '''OUPUT can be one of:
  FILENAME
  file:FILENAME
  dir:DIRNAME
  dir:DIRNAME:by_namespace=false:by_api_group_kind=false
'''

output_types = {
    'file': FileWriter,
    'dir': DirWriter,
}


def main():
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, epilog=output_arg_help)
    arg_parser.add_argument('--remove-namespace', action='store_true', help='remove namespace from objects')
    arg_parser.add_argument('--remove-tiller-labels', action='store_true', help='remove helm tiller labels')
    arg_parser.add_argument('--log-level', default='WARNING')
    arg_parser.add_argument('inputs', metavar='INPUT', nargs='*', help='file or directory name')
    arg_parser.add_argument('output', metavar='OUTPUT', help='see below for formats')
    args = arg_parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=args.log_level)

    inputs = args.inputs
    if not inputs:
        inputs = [sys.stdin]

    cleaner = Cleaner()
    cleaner.remove_namespace = args.remove_namespace
    cleaner.remove_tiller_labels = args.remove_tiller_labels

    try:
        writer = parse_smart_arg(args.output, output_types, FileWriter)
    except Exception:
        return arg_parser.error('Invalid OUTPUT format')

    for input in inputs:
        reader = get_reader(input)
        for obj in reader:
            obj = cleaner.process(obj)
            writer.write(obj)


def parse_smart_arg(arg, class_map, default_class=None):
    parts = arg.split(':')
    if len(parts) == 1:
        return default_class(parts[0])
    class_name = parts[0]
    klass = class_map[class_name]
    main_arg = parts[1]
    if len(parts) > 2:
        kwargs = parse_smart_kwargs(parts[2:])
    else:
        kwargs = {}
    return klass(main_arg, **kwargs)


def parse_smart_kwargs(parts):
    kwargs = {}
    for part in parts:
        k, v = part.split('=', maxsplit=1)
        kwargs[k] = yaml.load(v)
    return kwargs


if __name__ == '__main__':
    main()
