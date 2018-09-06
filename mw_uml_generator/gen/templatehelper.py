from jinja2 import FileSystemLoader,Environment
import os,sys
def check_and_createpath(file_path):
    if not os.path.exists(file_path):
        os.makedirs(file_path)

def add_path_splash(file_path):
    return file_path if file_path.endswith('/') else file_path+'/'


TemplatePath =os.path.join( os.path.dirname(__file__),'template')
load = FileSystemLoader(TemplatePath)
templateEnv =Environment(loader=load)
templateEnv.trim_blocks = True
templateEnv.lstrip_blocks = True

def save_file_by_template(temp_file,saved_file,over_write=True,**args):
    # _tmppath =temp_file.split('/')
    # tmp_file_name =_tmppath.pop()
    # tmp_file_path= '/'.join(_tmppath)
    # print([tmp_file_path,tmp_file_name])
    t = templateEnv.get_template(temp_file)
    (file_path,filename)=os.path.split(saved_file)
    check_and_createpath(file_path)
    if not over_write and os.path.exists(saved_file):
        saved_file=saved_file+'.new'
    render_txt = t.render(**args)

    with open(saved_file, 'w',encoding='utf-8') as f:
        f.write(render_txt)