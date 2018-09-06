from jinja2 import FileSystemLoader,Environment
import os
import json

TemplatePath = os.path.dirname(__file__)

load = FileSystemLoader([TemplatePath])
templateEnv =Environment(loader=load)
templateEnv.trim_blocks = True
templateEnv.lstrip_blocks = True

def genTemplate(templateName,**args):
    t =templateEnv.get_template('%s.tpl' % templateName)
    return t.render(args)

def project_mdj(project_name):
    with open(os.path.join(TemplatePath,'mdj/template.mdj')) as f:
        data =json.loads(f.read())
        data['name']=project_name
        return json.dumps(data)



def gencode_yml(**opts):
    # uml_file =opts['uml']
    return genTemplate('gencode',**opts)

def gitignore(extends=''):
    return genTemplate('.gitignore', extends =extends)

def requirements(extends):
    return genTemplate('requirements',extends =extends)




