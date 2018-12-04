from ..uml_parser import uml_loads
from .parse_rule import SwaggerHandle,ModelHandle
from ..template import gitignore,genTemplate,requirements

from ..fileutils import FileOp
import os
class Generate():
    def __init__(self,opts):
        filename = opts['uml']
        self.parser =uml_loads(filename)
        self.root =self.parser.root
        self.options =opts or {}
        self.modelhandle = self.create_model_handle()
        self.swaggerhandle =self.create_swagger_handle()

        md = opts.get('markdown')
        if md:
            for key,v in md.items():
                self.swaggerhandle.md2swagger(os.path.abspath(v),key)

    def create_model_handle(self):
        return ModelHandle(self.parser,**(self.options.get('model') or {}))
    def create_swagger_handle(self):
        return SwaggerHandle(self.parser,**(self.options.get('swagger') or {}))

    def render_aiohttp(self):
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


        if self.options.get('flag','')=='table':
            self.modelhandle.gen_table_define(aio_struct['app'])
        else:
            self.swaggerhandle.gen_aiohttps(aio_struct['app'])

        return aio_struct

