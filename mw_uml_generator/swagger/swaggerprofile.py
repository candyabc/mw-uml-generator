
import yaml
from typing import (List)
# from ..template import genTemplate
# from ..fileutils import FileOp
from .yaml_orderdictex import OrderDictEx
in_params_map = {'h': 'header',
                 'p': 'path',
                 'q': 'query',
                 'b': 'body',
                 'f': 'formData'}
SS_FILE_IMG ='img'
SS_FILE_PDF = 'pdf'
SS_FILE_EXCEL = 'excel'

def parse_directive(text):
    re ={}

    directives =text.split('/')
    if 'req' in directives:
        re['required']=True
    xins =list(set(in_params_map.keys())& set(directives))
    if len(xins)>0:
        re['xin']=in_params_map.get( xins[0])
    return re

def ref_define(name):
    return {'$ref': '#/definitions/%s' % name.capitalize()}
class SSParam:
    def __init__(self, name, description,schema=None, required=True,**args):
        self.name = name
        self.description = description
        self.required = required
        self.schema =schema

class SSParamSchema:
    def __init__(self, name, format='', isarray=False, isref=False,**args):

        self.name = name
        self.format = format
        self.isarray = isarray
        self.isref = isref
        try:
            self.enum_define = args.pop('enum_define')
        except:
            self.enum_define=None
        self.file_types =[]
        self.extra =args or {}

    def render(self, paramCls):
        def ref_style():
            return ref_define(self.name)

        def array_style():
            return {"type": "array", "items": ref_style() if self.isref else self.name}

        if not self.isarray and not self.isref:
            re = {'type': self.name, 'format': self.format}
            if self.enum_define is not None:
                re.pop('format')
                re.update({'enum':[literal[0] for literal in self.enum_define.literals]})
            re.update(self.extra)

        else:
            re = {"schema": array_style() if self.isarray else ref_style()}

        if paramCls ==SSDefineParam:
            if 'schema' in re.keys():
                re = re.pop('schema')
        elif paramCls == SSResponseParam:
            if not 'schema' in re.keys():
                re.pop('format')
                re = {'schema': re}

        return re

class SSInParam(SSParam):
    def __init__(self, name, description, xin=None, **args):
        super().__init__(name, description, **args)
        self.xin = xin

    def render(self):
        re = OrderDictEx({
            'in': self.xin,
            'name': self.name,
            'description': self.description,
            'required': self.required,
        })
        re.update(self.schema.render(self.__class__))
        return re


class SSDefineParam(SSParam):
    def render(self):
        re = {'description': self.description}
        if type(self.schema)==SSParamSchema:
            re.update(self.schema.render(self.__class__))
        else:
            re.update(self.schema.render())
        return OrderDictEx(re)


class SSResponseParam(SSParam):
    headers = List[SSDefineParam]

    def __init__(self, name, description, **args):
        super().__init__(name, description, **args)
        self.headers = []
        self.file_type=None # schema == file时的类别

    def render(self):
        re = {'description': self.description}
        if len(self.headers) > 0:
            re.update({"headers": {header.name: header.render() for header in self.headers}})
        if self.schema:
            re.update(self.schema.render(self.__class__))

        return OrderDictEx(re)


class SSDefine():
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.params = []
        self.discriminator =None
        self.allOf=[]

    def render(self):
        re = OrderDictEx({"type": "object",
                          "description": self.description
                          })

        required = [param.name for param in self.params if param.required]
        if self.discriminator is not None:
            re.update({'discriminator':self.discriminator})
            if not (self.discriminator in required):
                required.append(self.discriminator)
        if len(required) > 0:
            re.update({'required': required})
        if len(self.params) > 0:
            re.update({"properties": {param.name: param.render() for param in self.params}})
        if len(self.allOf)>0:
            desc = re.pop('description')
            allof_item = re
            re ={'description': desc,
                 'allOf':[ref_define(item) for item in self.allOf] +[allof_item]}

        return re

class SSNonameDefine(SSDefine):
    def __init__(self, description):
        super().__init__('noname',description)


class SSoperation():
    in_params = List[SSInParam]
    re_params = List[SSResponseParam]

    def __init__(self, method, pathname, tag, summary='', description=''):
        self.tag = tag
        self.pathname = pathname
        self.method = method
        self.summary = summary
        self.description = description
        self.in_params = []
        self.re_params = []
        self.consumes =[]
        self.produces = []

    @property
    def operatorid(self):
        return '%s%s' % (self.method, self.pathname.replace('/', '_').replace('{', '').replace('}', ''))

    def analysis(self):
        '''
        分析operation的params，并修改mimetype
        :return: 
        '''
        form_params = filter(lambda param:param.xin ==in_params_map.get('f'),self.in_params)
        if len(list(filter(lambda param:param.schema.name == 'file', form_params)))>0:
            self.consumes.append('multipart/form-data')
        else:
            self.consumes.append('application/x-www-form-urlencoded')

        body_params = list(filter(lambda param: param.xin == in_params_map.get('b'),self.in_params) )
        if len(body_params)>0:
            if body_params[0].schema.name in ('integer','string'):
                self.consumes.append('text/plain; charset=utf-8')

        re_params =filter(lambda param:param.schema.name =='file',self.re_params)
        if len(re_params):
            for re_param in re_params:
                if SS_FILE_IMG in re_param.schema.file_types:
                    self.produces += ['image/png','image/gif','image/jpeg']
                if SS_FILE_PDF in re_param.schema.file_types:
                    self.produces.append('application/pdf')
                if SS_FILE_EXCEL in re_param.schema.file_types:
                    self.produces.append('application/vnd.ms-excel')

    def render(self, paths, operationid_prefix):
        paths[self.pathname] = paths.get(self.pathname) or {}

        full_operationid = '%s.%s' % (operationid_prefix, self.operatorid)

        operation_schema = paths[self.pathname][self.method] = OrderDictEx({
            "summary": self.summary,
            "tags": [self.tag],
            "schemes": ['http', 'https'],
            "description": self.description,
            "consumes": self.consumes,
            "produces": self.produces,
            "operationId": full_operationid,
            "parameters": [param.render() for param in self.in_params],
            "responses": {
                param.name: param.render() for param in self.re_params
            }})
        if len(self.consumes)==0:
            operation_schema.pop('consumes')
        if len(self.produces) == 0:
            operation_schema.pop('produces')

class SStag:
    def __init__(self, name, description):
        self.name = name
        self.description = description
def split_title(txt):
    if txt.endswith(')'):
        index = txt.rfind('(')
        if index>0:
            return txt[index +1:-1] ,txt[:index].strip()


    return txt,txt

class SwaggerProfile():
    basepath = str
    schema = OrderDictEx
    ver = str
    name = str

    def __init__(self, name, basepath, title=''):
        self.name = name
        self.basepath = basepath
        self.host = 'localhost:8080'
        # self.ver = basepath.split('/')[-1]
        self.title = title
        self.operations = []
        self.definitions = []
        self.tags = []
        self.consumes = ['application/json']
        self.produces = ['application/json']

    @property
    def ver(self):
        return  self.basepath.split('/')[-1] if self.basepath!='' else 'v1'

    @property
    def model_name(self):

        return '%s_%s' % (self.name, self.ver)

    def model_routename(self):
        return '%s_routes' % self.model_name

    def dump_to(self, filename):
        s = self.dump()
        with open(filename, mode='w') as f:
            f.write(s)


    def dump(self):
        self.render()
        re = yaml.dump(self.schema, default_flow_style=False)
        s = re.encode('utf-8').decode('unicode_escape')
        # re =yaml.dump_all([{k:v} for k,v in self.schema.items()],default_flow_style=False)
        # re =re.replace('---\n','',len(self.schema.keys()))
        return s

    def render(self):
        paths = {}
        for operation in self.operations:
            operation.render(paths, 'app.apis.{model_name}.{tag}'.format(
                model_name=self.model_name,
                tag=split_title(operation.tag)[0]))

        self.schema = OrderDictEx({
            "swagger": "2.0",
            "info": {
                "title": self.title,
                "version": self.ver
            },
            "consumes":self.consumes,
            "produces":self.produces,
            "basePath": self.basepath,
            "tags": [OrderDictEx({'name': tag.name, 'description': tag.description}) for tag in self.tags],
            "paths": paths,
            "definitions": {define.name.capitalize(): define.render() for define in self.definitions}})

