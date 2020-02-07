from ..uml_parser import uml_loads,UmlModel
from ..swagger.uml_to_profile import DBModelProfile,ModelSwaggerProfile
from ..template import gitignore,genTemplate,requirements
from ..markdown import MdTemplateParser
from ..fileutils import FileOp
import os
from .._singleton import Singleton

def get_project_name():
    cwd = os.getcwd()
    return cwd.split('\\')[-1]

def get_project_root():
    project_name = get_project_name()
    project_name = project_name.split('/')[-1]
    return project_name.replace('-', '_')

class GenerateFactory(metaclass=Singleton):
    def __init__(self):
        self._gens ={}
    def registor(self,cls):
        if cls.up_type is not None:
            self._gens[cls.up_type]= cls

    def generate(self,up_type,opts):
        cls = self._gens.get(up_type)
        if cls is None:
            raise Exception('generate not support type:%s' % up_type)
        generator =cls(opts)
        return generator.generate()

def generate_struct(up_type,opts):
    factory = GenerateFactory()
    return factory.generate(up_type,opts)

class GenerateType(type):
    _factory = GenerateFactory()
    def __new__(cls, name, bases, attrs):
        new_cls = super(GenerateType, cls).__new__(cls, name, bases, attrs)
        cls._factory.registor(new_cls)
        return new_cls


class BaseGenerate(metaclass=GenerateType):
    up_type =None
    def __init__(self,opts):
        self.opts = opts

    def generate_project(self,ignore_data='',readme_data='',requirement_data =''):
        file_st = {}
        file_st['.gitignore'] = (gitignore(ignore_data), FileOp.NO_OVERWRITE)
        file_st['README.md'] = (readme_data, FileOp.NO_OVERWRITE)
        file_st['requirements.txt'] = (requirements(requirement_data), FileOp.NO_OVERWRITE)

        return file_st


    def generate(self):
        pass

class DockerGenerate(BaseGenerate):
    up_type = 'docker'
    def generate(self):
        project_name = get_project_name()
        envs = self.opts.get('env') or {}
        ver = self.opts['args'].get('version')
        docker_struct = \
            {'docker-compose.yml': (
            genTemplate('docker-compose', envs=envs , project=project_name,version = ver), FileOp.CREATE_NEW),
             'run.sh': (genTemplate('run_sh', envs=envs), FileOp.CREATE_NEW)}

        return docker_struct


class Generate(BaseGenerate):
    def __init__(self,opts):
        filename = opts['uml']
        self.parser =uml_loads(filename)
        self.root =self.parser.root
        self.options =opts or {}
        self.db_model =None
        self.swaggers =[]
        self.as_model =True
        if self.options.get('model') is not None:
            try:
                self.as_model = self.options['model'].pop('as_model')
            except:
                pass


    def load_models(self):
        _db_models = self.get_models('model')
        if len(_db_models)>0:
            self.db_model =self.create_model(_db_models[0])

        _swagger_models = self.get_models('swagger')
        for sw_model in _swagger_models:
            self.swaggers.append(self.create_swagger(sw_model))

        md= self.get_markdown()
        if md is not None:
            self.swaggers+=self.create_swagger_from_md(md)


    def get_models(self,style_name):
        return self.root.search(lambda el: type(el) == UmlModel and el.name == style_name)

    def create_model(self,model):
        db_profile = DBModelProfile()
        db_profile.load_from_uml(model,**self.options.get('model',{}))
        return db_profile

    def create_swagger(self,model):
        profile =ModelSwaggerProfile()
        profile.load_from_uml(model,**self.options.get('swagger') or {})
        return profile

    def get_markdown(self):
        return self.options.get('markdown')

    def create_swagger_from_md(self,md):
        ret =[]
        for key,v in md.items():
            profile = ModelSwaggerProfile()
            profile.name = key
            parser = MdTemplateParser(profile)
            parser.parse(os.path.abspath(v))
            ret.append(profile)
        return ret

    def generate_models(self,db_model):
        if self.as_model:
            return {'model_base.py': (db_model.gen_db_model_base(), FileOp.OVERWRITE),
                                'models.py': (db_model.gen_db_model(), FileOp.NO_OVERWRITE)}
        else:
            return {'models.py': (db_model.gen_db_tables(), FileOp.OVERWRITE)}


AIOHTTP_REQUIREMENTS ='''
aiohttp
aiohttp-swagger
# aioredis
#python-memcached
             '''

class AioHttpGenerate(Generate):
    up_type = 'aiohttp'
    def generate(self):
        self.load_models()
        file_st =self.generate_project(requirement_data=AIOHTTP_REQUIREMENTS)

        app_st =file_st['app']={}
        app_st['main.py'] = (genTemplate('aiohttp/main', swaggers=self.swaggers), FileOp.NO_OVERWRITE)
        app_st['config.py']=(genTemplate('aiohttp/config'), FileOp.NO_OVERWRITE)
        app_st['__init__.py'] =('', FileOp.NO_OVERWRITE)
        if self.db_model:
            app_st['models']= self.generate_models(self.db_model)


        swagger_st = app_st['swagger']={}
        for swagger in self.swaggers:
            app_st.update(swagger.gen_aio_controls())
            swagger_st['%s.yaml' % swagger.name] =(swagger.dump(), FileOp.OVERWRITE)
        return file_st

class BlankGenerate(Generate):
    up_type = 'blank'
    def generate(self):
        self.load_models()
        file_st = self.generate_project()
        project_root = get_project_root()
        project_st=file_st[project_root]={}
        if self.db_model:
            project_st['models']= self.generate_models(self.db_model)

        return file_st

class ConfigGenerate(Generate):
    up_type = 'config'
    def generate(self):
        self.load_models()
        file_st = self.generate_project()
        project_root = get_project_root()
        project_st = file_st[project_root] = {}
        if self.db_model:
            project_st['models']= self.generate_models(self.db_model)

        return file_st

