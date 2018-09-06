from ..uml_parser import uml_loads
from .parse_rule import SwaggerHandle,ModelHandle
from ..template import gitignore,genTemplate,requirements

from ..fileutils import FileOp
class Generate():
    def __init__(self,filename,opts=None):
        self.parser =uml_loads(filename)
        self.root =self.parser.root
        self.options =opts
        self.modelhandle = self.create_model_handle()
        self.swaggerhandle =self.create_swagger_handle()

    def create_model_handle(self):
        return ModelHandle(self.parser,**(self.options or {}))
    def create_swagger_handle(self):
        return SwaggerHandle(self.parser,**(self.options or {}))

    def render_aiohttp(self,**args):
        # option =(self.options or {}).update(args)
        #todo:option
        aio_struct = {
            '.gitignore': (gitignore(),FileOp.NO_OVERWRITE),
            'requirements.txt': (requirements('''
aiohttp
aiohttp-swagger
# aioredis
# mwutils
# ujson
uvloop
#python-memcached
            '''),FileOp.NO_OVERWRITE),
            'run.py': (genTemplate('aiohttp/run'), FileOp.NO_OVERWRITE),
            'app':{}
            }

        self.swaggerhandle.gen_aiohttps(aio_struct['app'])
        self.modelhandle.gen_aiohttp(aio_struct['app'])
        return aio_struct

