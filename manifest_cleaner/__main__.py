import sys
import logging
import argparse

from .reader import FileReader, get_path_reader
from .cleaner import Cleaner
from .writer import FileWriter, DirWriter


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-i', '--input', help='input file or directory (default stdin)')
    arg_parser.add_argument('-o', '--output', help='ouput file (default stdout)')
    arg_parser.add_argument('-d', '--output-dir', help='output directory')
    arg_parser.add_argument('--remove-namespace', action='store_true', help='remove namespace from objects')
    arg_parser.add_argument('--remove-tiller-labels', action='store_true', help='remove helm tiller labels')
    arg_parser.add_argument('--log-level', default='WARNING')
    args = arg_parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=args.log_level)

    if args.output and args.output_dir:
        arg_parser.error('You must specify either --output or --output-dir')

    if args.input:
        reader = get_path_reader(args.input or sys.stdin)
    else:
        reader = FileReader(sys.stdin)

    cleaner = Cleaner()
    cleaner.remove_namespace = args.remove_namespace
    cleaner.remove_tiller_labels = args.remove_tiller_labels

    if args.output:
        writer = FileWriter(args.output)
    elif args.output_dir:
        writer = DirWriter(args.output_dir)
    else:
        writer = FileWriter(sys.stdout)

    for obj in reader:
        obj = cleaner.process(obj)
        writer.write(obj)


if __name__ == '__main__':
    main()
