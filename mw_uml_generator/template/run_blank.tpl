from argparse import ArgumentParser
from {{ project_root }} import main
if __name__ == '__main__':
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--test ] [--help]'
    )
    arg_parser.add_argument('-t', '--test',type=bool, default=False, help='test')
    options = arg_parser.parse_args()
    main(options)