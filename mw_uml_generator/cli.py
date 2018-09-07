from __future__ import division, print_function, absolute_import
import click
import sys
import logging
from . import __version__
from .import create_project,up_project,gen_docker


def get_version(ctx, param, value):
    # print([ctx,param,value])
    if value:
        click.echo('mw_uml_generator {ver}'.format(ver=__version__))
        sys.exit(0)

def setup_logging(ctx, param, value):
    """Setup basic logging 
    """
    loglevel = logging.DEBUG if value else logging.INFO
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('-v','--version',is_flag =True,callback=get_version,help="show version",expose_value=False,is_eager =True,required=False )
@click.option('-vv','--very-verbose',is_flag=True,callback=setup_logging,help="debug mode",expose_value=False,is_eager =True,required=False)
def cli():
    pass

@cli.command()
@click.argument('project_name')
def create(project_name):
    create_project(project_name)

@cli.command()
@click.option('--typ',type=str,default ='aiohttp',help='工程类别 aiohttp | flask')
@click.option('--force',type=bool,default =False ,help='是否强制全覆盖所有文件')
def up(typ ,force =False):
    up_project(typ)

@cli.command()
def docker():
   gen_docker()


if __name__ == "__main__":
    cli()
