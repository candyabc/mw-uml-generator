import os,sys
from ..fileutils import update_save_file,create_directory,FileOp

from ..template import project_mdj,gencode_yml,genTemplate
from .generate import Generate
from six import iteritems
import yaml


CONFIG_FILE ='./gencodeFile.yml'


def read_configfile():
    if not os.path.exists(CONFIG_FILE):
        sys.exit('%s 不存在,请先执行 gencode create project.'% CONFIG_FILE)
    with open(CONFIG_FILE) as f:
        return yaml.load(f.read())

def write_configfile(cf):
    with open(CONFIG_FILE,mode='w') as f :
        yaml.dump(cf,f,default_flow_style=False)

def save_structure(root_path,structure):
    def save_struct_dict(fullpath,struct_dict):
        for key, value in iteritems(struct_dict):
            if type(value) == dict:
                path0 =os.path.join(fullpath,key)
                create_directory(path0)
                save_struct_dict(path0,value)
            else:
                if type(value)==tuple:
                    update_save_file(os.path.join(fullpath,key),*value)
                else:
                    update_save_file(os.path.join(fullpath, key), value)

    save_struct_dict(root_path,structure)


# def init_file(opts):
#     update_save_file(CONFIG_FILE,gencodeFile(opts))


def create_project(project_name):
    if (project_name or '' )=='':
        sys.exit('please input project name.')

    cwd =os.getcwd()

    if os.path.exists(os.path.join(cwd,project_name)):
        sys.exit('%s already exists.' % project_name)

    cwd = os.getcwd()
    project_struct ={
        project_name:{
            'files':{'%s.mdj' % project_name:project_mdj(project_name)},
            'gencodeFile.yml':gencode_yml(uml_file ='./files/%s.mdj' %(project_name))
        }
    }

    save_structure(cwd,project_struct)

def up_project(project_type =None):
    opts =read_configfile()
    _p_type = project_type or opts.get('project')
    if _p_type ==None:
        sys.exit('please set project type,use gencode up --type aiohttp|flask')
    opts['project']= _p_type
    write_configfile(opts)

    if _p_type =='flask':
        create_flask()
    elif _p_type =='aiohttp':
        create_aiohttp()
    else:
        sys.exit('not support this type:%s' % project_type)


def create_aiohttp():
    opts =read_configfile()
    generate = Generate(opts['uml'])
    cwd = os.getcwd()

    save_structure(cwd,generate.render_aiohttp())

def gen_docker():
    opts = read_configfile()
    cwd = os.getcwd()
    project_name = cwd.split('\\')[-1]
    project_name = project_name.split('/')[-1]
    project_name =project_name.replace('-','_')
    docker_struct =\
        {'docker-compose.yml':(genTemplate('docker-compose',envs =opts.get('env') or {},project = project_name),FileOp.NO_OVERWRITE),
         'run.sh':(genTemplate('run_sh',envs =opts.get('env') or {}),FileOp.NO_OVERWRITE)}
    save_structure(cwd, docker_struct)

# def create_swaggergen(opts):
#     swaggergen = SwaggerGen(opts['umlfile'])
#     options = opts.get('swagger', {})
#     options['service'] = opts.get('service')
#     swaggergen.generate(options)
#     return swaggergen

# def create_modelgen(opts):
#     modelgen = DataModelGen(opts['umlfile'])
#     modelgen.generate(opts.get('id'))
#     return modelgen

# def create_aiohttp():
#     pass
#     opts =read_configfile()
#     swaggergen = create_swaggergen(opts)
#     aio_struct ={
#         '.gitignore':(gitignore([])),
#         'requirements.tpl':(read_file_data('aiohttp/requirements.tpl')),
#         opts['service']:{}
#     }
#     service =aio_struct[opts['service']]
#     if len(swaggergen.swaggers)>0:
#         swagger =swaggergen.swaggers[0]
#         service.update({'swagger': swagger.render_swagger()})
#         service.update(swagger.render_aiohttpservice())
#
#     modelgen = create_modelgen(opts)
#     if len(modelgen.schemas) > 0:
#         schema =modelgen.schemas[0]
#         service.update(schema.render_models())
#     save_structure(opts['projectPath'],aio_struct)

def create_flask():
    pass
    # opts =read_configfile()
    #
    # flask_struct ={
    #     '.gitignore':(gitignore([])),
    #     'requirements.tpl':(read_file_data('flask/requirements.tpl')),
    #     'run_sh.tpl':(flask_run(opts)),
    #     'config.tpl.py':(read_file_data('flask/config.tpl.pys')),
    #     opts['service']:{
    #         '__init__.py':(read_file_data('flask/app/__init__.pys'))
    #     }
    # }
    #
    #
    # service = flask_struct[opts['service']]
    #
    # modelgen = create_modelgen(opts)
    # if len(modelgen.schemas) > 0:
    #     schema =modelgen.schemas[0]
    #     flask_struct.update(schema.render_schema())
    #     service.update(schema.render_flask_models())
    #
    # swaggergen = create_swaggergen(opts)
    # if len(swaggergen.swaggers)>0:
    #     swagger =swaggergen.swaggers[0]
    #     service.update({'swagger':swagger.render_swagger()})
    #     service.update(swagger.render_flaskcontrolls())
    #
    # save_structure(opts['projectPath'],flask_struct)



