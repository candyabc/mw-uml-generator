import os,sys
from ..fileutils import update_save_file,create_directory,FileOp
from ..log import logger
from ..template import project_mdj,gencode_yml,genTemplate,gitignore,requirements,run_blank,readme
from .generate import Generate
from six import iteritems
import yaml
import requests
from .swagger2api import swagger2api


CONFIG_FILE ='./gencodeFile.yml'


def read_configfile():
    if not os.path.exists(CONFIG_FILE):
        sys.exit('%s 不存在,请先执行 gencode create project.'% CONFIG_FILE)
    with open(CONFIG_FILE) as f:
        return yaml.load(f.read())
#
# def write_configfile(cf):
#     with open(CONFIG_FILE,mode='w') as f :
#         yaml.dump(cf,f,default_flow_style=False)

def save_structure(root_path,structure,overwrite =False):
    def save_struct_dict(fullpath,struct_dict):
        for key, value in iteritems(struct_dict):
            if type(value) == dict:
                path0 =os.path.join(fullpath,key)
                create_directory(path0)
                save_struct_dict(path0,value)
            else:
                if type(value)==tuple:
                    ( content, opType )= value
                    update_save_file(os.path.join(fullpath,key),content, opType ,overwrite=overwrite)
                elif type(value)==str:
                    update_save_file(os.path.join(fullpath, key), value,overwrite = overwrite)
                else:
                    raise Exception('save_structure not support :%s' % value)
    save_struct_dict(root_path,structure)


# def init_file(opts):
#     update_save_file(CONFIG_FILE,gencodeFile(opts))

def get_project_root(cwd):
    project_name = cwd.split('\\')[-1]
    project_name = project_name.split('/')[-1]
    return project_name.replace('-', '_')

def create_project(project_name,template):
    logger.report('run','create project: %s from %s' % (project_name,template))
    if (project_name or '' )=='':
        sys.exit('please input project name.')

    cwd =os.getcwd()

    if os.path.exists(os.path.join(cwd,project_name)):
        sys.exit('%s already exists.' % project_name)

    cwd = os.getcwd()
    project_struct ={
        project_name:{
            'files':{'%s.mdj' % project_name:project_mdj(project_name)},
            'gencodeFile.yml':gencode_yml(uml_file ='./files/%s.mdj' %(project_name),project = template)
        }
    }
    # if typ =='blank':
    #     project_struct[project_name].update()
    save_structure(cwd,project_struct)

    logger.info('create project %s finished.' % project_name)

def up_temp_blank(project_name,opts):
    main_py ='''
def main():
    pass                                         
'''
    project_root = get_project_root(project_name)
    return {project_root:{'__init__.py':('',FileOp.NO_OVERWRITE),
                          'main.py':(main_py,FileOp.NO_OVERWRITE)},
            '.gitignore':(gitignore(),FileOp.NO_OVERWRITE),
            'requirements.txt':(requirements(),FileOp.NO_OVERWRITE),
            'README.md':(readme(project_name),FileOp.NO_OVERWRITE),
            'run.py':(run_blank(project_root),FileOp.NO_CREATE)}

def up_temp_config(project_name,opts):
    project_struct =up_temp_blank(project_name,opts)
    project_root = get_project_root(project_name)
    project_struct[project_root].update({'config.py':(genTemplate('config'),FileOp.NO_OVERWRITE)})
    return project_struct

def init_config():
    logger.report('run', 'init config file')
    cwd = os.getcwd()
    update_save_file(os.path.join(cwd,'gencodeFile.yml'),
    gencode_yml(uml_file ='',project = 'blank'))

def up_project(overwrite = False):
    logger.report('run','up generate ')
    opts =read_configfile()
    _p_type = opts.get('project')
    if _p_type ==None:
        sys.exit('please set project type,use gencode up --type aiohttp|blank|config')
    cwd = os.getcwd()
    project_name = cwd.split('/')[-1]
    if _p_type =='aiohttp':
        project_struct= create_aiohttp(opts)
    elif _p_type =='blank':
        project_struct = up_temp_blank(project_name,opts)
    elif _p_type == 'config':
        project_struct = up_temp_config(project_name,opts)
    else:
        sys.exit('not support this type:%s' % _p_type)

    save_structure(cwd,project_struct,overwrite)
    logger.info( 'up generate finished')

def create_aiohttp(opts):
    generate = Generate(opts)
    return generate.render_aiohttp()

def gen_docker():
    try:
        opts = read_configfile()
        envs = opts.get('env')
    except:
        envs = None

    cwd = os.getcwd()
    project_root =get_project_root(cwd)
    docker_struct =\
        {'docker-compose.yml':(genTemplate('docker-compose',envs =envs or {},project = project_root),FileOp.CREATE_NEW),
         'run.sh':(genTemplate('run_sh',envs =opts.get('env') or {}),FileOp.CREATE_NEW)}
    save_structure(cwd, docker_struct)


def isBlank(v):
    return v in [None,'']
def gen_apijs(name,infile,outfile):
    logger.report('run', 'run swagger2api name %s ,in:%s:out:%s' % (name,infile,outfile))
    try:
        opts = read_configfile()
        apijs = opts.get('apijs')
    except:
        apijs = None
    if name:
        if apijs is None:
            sys.exit('%s不存在或设定apijs不存在' % CONFIG_FILE)
        cf = apijs.get(name)
        if cf is None:
            sys.exit('apijs.%s 未设定 ')
        if isBlank(cf.get('in')):
            sys.exit('参数apijs.%s.in未设定' % name)
        if isBlank(cf.get('out')) and isBlank(apijs.get('outPath')):
            sys.exit('请设定参数apijs.%s.out或 apijs.outPath' % name)
        infile = cf['in']
        outpath = os.path.abspath( apijs['outPath'])
        outfile =os.path.join(outpath,('%s.js' % name)) if isBlank(cf.get('out')) else os.path.abspath(cf['out'])

        # outfile =os.path.join( os.path.abspath( apijs['outPath']),('%s.yml' % name)) if cf.get('out','') =='' else os.path.abspath(cf.get['out'])
    else:
        if isBlank(infile):
            sys.exit('请设定 -i 参数')
        if isBlank(outfile) :
            sys.exit('请设定 -o 参数')

    #检查infile的类别，可以从http或本地文件读取
    if infile.startswith('http'):
        res =requests.get(infile)
        if res.status_code!=200:
            sys.exit('fetch %s 失败,%s' % (infile,res.text))
        else:
            swagger =res.json()
    else:
        if not os.path.exists(os.path.abspath(infile)):
            sys.exit('in file:%s不存在' % infile)
        with open(os.path.abspath(infile)) as f:
            swagger = yaml.load(f.read())
    swagger2api(swagger, outfile)
    logger.report('invoke','产生%s完成' % outfile)
    # if infile is None:
    #     for _infile,_outfile in apijs.items():
    #         swagger2api(_infile,outfile)
    # else:
    #     swagger2api(infile,outfile)