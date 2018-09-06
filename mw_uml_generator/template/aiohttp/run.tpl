from .app.main import main
from argparse import ArgumentParser
if __name__ == '__main__':
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--mode ] [--help]'
    )
    arg_parser.add_argument('-m', '--mode', default='default',type=str, help='service run mode eg.test| production ...')
    options = arg_parser.parse_args()

    main(options.__dict__)
