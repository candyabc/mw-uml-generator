from __future__ import division, print_function, absolute_import
import click
import sys
import logging
from . import __version__
from .import create_project,up_project,gen_docker,gen_apijs,init_config
from .log import configure_logger


def get_version(ctx, param, value):
    # print([ctx,param,value])
    if value:
        click.echo('mw_uml_generator {ver}'.format(ver=__version__))
        sys.exit(0)

def setup_logging(ctx, param, value):
    """Setup basic logging 
    """
    loglevel = logging.DEBUG if value else logging.INFO
    configure_logger({'log_level':loglevel})
    # logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    # logging.basicConfig(level=loglevel, stream=sys.stdout,
    #                     format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('-v','--version',is_flag =True,callback=get_version,help="show version",expose_value=False,is_eager =True,required=False )
@click.option('-vv','--very-verbose',is_flag=True,callback=setup_logging,help="debug mode",expose_value=False,is_eager =True,required=False)
def cli():
    pass

@cli.command()
@click.argument('project_name')
@click.option('-t','--template',type=str,default ='aiohttp' ,help='创建event的模板,aiohttp|blank|config')
def create(project_name,template):
    create_project(project_name,template)

@cli.command()
# @click.option('--typ',type=str,default ='aiohttp',help='工程类别 aiohttp | flask')
@click.option('-f','--flag',type=str,help='')
@click.option('-o','--overwrite',type=bool,default =False ,help='是否强制全覆盖所有文件')

def up(flag=None,overwrite=False):
    up_project(overwrite,flag=flag)

@cli.command()
def docker():
   gen_docker()

@cli.command()
@click.option('-n','--name',type=str,help='在 config 文件 apijs设定的名称')
@click.option('-i','--in','--infile',type=str,help='in swagger file')
@click.option('-o','--out','--outfile',type=str,help='out api.js file')
def apijs(name=None,infile=None,outfile=None):
    gen_apijs(name,infile,outfile)

@cli.command()
def init():
    init_config()
if __name__ == "__main__":
    cli()
