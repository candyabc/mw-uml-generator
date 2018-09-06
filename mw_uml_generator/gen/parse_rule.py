# from ..uml_parser import (UmlModel,UmlSignal,UmlPrimitiveType,UmlClass,UmlAssociation,
#                           UmlAssociationClassLink,UmlEnumeration,AssociationType,ge)
from ..uml_parser import *
# from collections import OrderedDict
import re
import yaml
from typing import (List)
from ..template import genTemplate
from ..fileutils import FileOp
from ..yaml_orderdictex import OrderDictEx
from enum import Enum

#model 里 stereotype对应的参数类型
in_params_map = {'h': 'header',
           'p': 'path',
           'q': 'query',
           'b': 'body',
           'f': 'form'}

def get_sw_type_format(atype):
    '''
    根据 model里的类型转成 swagger 的类型及 format格式
    :param atype: 
    :return: 
    '''
    atype=atype.lower().strip()
    if atype == 'integer':
        return 'integer', 'int32'
    elif atype == 'long':
        return 'integer', 'int64'
    elif atype == 'float':
        return 'number', 'float'
    elif atype == 'double':
        return 'number', 'double'
    elif atype == 'string':
        return 'string', ''
    elif atype == 'byte':
        return 'string', 'byte'
    elif atype == 'binary':
        return 'string', 'binary'
    elif atype == 'boolean':
        return 'boolean', ''
    elif atype == 'date':
        return 'string', 'date'
    elif atype in ('datetime', 'tdatetime'):
        return 'string', 'date-time'
    elif atype == 'password':
        return 'string', 'password'
    elif atype == 'file':
        return 'file', ''
    else:
        assert False, 'swagger type not support :%s' % type
        # return atype, ''

def convert_pathname(pathname):
    '''
    将pathname转换成swagger中标准的path，如 {company_id}_task_{id} 转换为{company_id}/task/{id}，注意{}里的_不做转换
    :param pathname: 
    :return: 
    '''
    params = re.findall('{\w+}', pathname)
    name =re.sub('{\w+}','%s',pathname).replace('_','/')
    return '/'+name % tuple(params)

class BaseGenerateHandle():
    def __init__(self,parser,**args):
        self.parser = parser
        self.root = self.parser.root

        self.options =self.default_options()
        self.options.update(args)

    def default_options(self):
        return {}

class SSParamSchema:
    def __init__(self,name,format='',isarray =False,isref =False):
        self.name =name
        self.format =format
        self.isarray = isarray
        self.isref = isref

    def render(self,param_style):
        def ref_style():
            return {'$ref': '#/definitions/%s' % self.name.capitalize()}
        def array_style():
            return {"type": "array","items": ref_style() if self.isref else self.name}

        if not self.isarray and not self.isref:
            re = {'type':self.name,'format':self.format}
        else:
            re = {"schema":array_style() if self.isarray else ref_style()}

        if param_style =='define':
            if 'schema' in re.keys():
                re =re.pop('schema')
        elif param_style =='return':

            if not 'schema' in re.keys():
                re.pop('format')
                re ={'schema':re}
        return re


class SSParam:
    def __init__(self,name,description,schema =None,required =True):
        self.name = name
        self.description = description
        self.schema =schema
        # self.xin =xin
        self.required =required

class SSInParam(SSParam):
    def __init__(self, name, description,xin =None,**args):
        super().__init__(name,description,**args)
        self.xin =xin
    def render(self):
        re = OrderDictEx({
            'in': self.xin,
            'name': self.name,
            'description': self.description,
            'required': self.required,
        })
        re.update(self.schema.render('in'))
        return re

class SSDefineParam(SSParam):
    def render(self):
        re = {'description': self.description}
        re.update(self.schema.render('define'))
        return OrderDictEx(re)

class SSResponseParam(SSParam):
    headers = List[SSDefineParam]
    def __init__(self, name, description,**args):
        super().__init__(name,description,**args)
        self.headers =[]

    def render(self):
        re = {'description': self.description}
        if len(self.headers)>0:
            re.update({"headers":{header.name:header.render() for header in self.headers}})
        if self.schema:
            re.update(self.schema.render('return'))
        return OrderDictEx(re)

class SSDefine():
    def __init__(self,name,description):
        self.name =name
        self.description = description
        self.params =[]

    def render(self):
        re =OrderDictEx({"type": "object",
         "description": self.description
         })
        required =[param.name for param in self.params if param.required]
        if len( required )>0:
            re.update({'required':required})
        if len(self.params)>0:
            re.update({"properties": {param.name:param.render() for param in self.params}})
        return re

class SSoperation():
    in_params =List[SSInParam]
    re_params =List[SSResponseParam]
    def __init__(self,method,pathname,tag,summary='',description=''):
        self.tag =tag
        self.pathname =pathname
        self.method =method
        self.summary = summary
        self.description =description
        self.in_params =[]
        self.re_params =[]

    @property
    def operatorid(self):
        return '%s%s'% (self.method,self.pathname.replace('/','_').replace('{','').replace('}',''))

    def render(self,paths,operationid_prefix):
        paths[self.pathname]=paths.get(self.pathname) or {}

        full_operationid='%s.%s' % (operationid_prefix,self.operatorid)
        paths[self.pathname][self.method] =OrderDictEx({
            "summary": self.summary,
            "tags": [self.tag],
            "schemes": ['http', 'https'],
            "description": self.description,
            "consumes": ["application/json"],
            "produces": ["application/json"],
            "operationId": full_operationid,
            "parameters": [param.render() for param in self.in_params],
            "responses": {
                param.name: param.render() for param in self.re_params
            }})

class SStag:
    def __init__(self,name,description):
        self.name =name
        self.description =description

class SwaggerProfile():
    basepath =str
    schema =OrderDictEx
    ver =str
    name =str
    def __init__(self,name,basepath,title=''):
        self.name =name
        self.basepath =basepath
        self.host ='localhost:8080'
        self.ver =basepath.split('/')[-1]
        self.title =title
        self.operations =[]
        self.definitions=[]
        self.tags=[]

    @property
    def model_name(self):
        return '%s_%s' %(self.name,self.ver)

    def model_routename(self):
        return '%s_routes' % self.model_name

    def dump_to(self,filename):
        self.render()
        yaml.dump(self.schema,open(filename,mode='w'),encoding='utf-8')
        # with open(filename,mode='w') as f :
            # for k,v in self.schema.items():
            #     yaml.dump({k:v},f,default_flow_style=False)

    def dump(self):
        self.render()
        re =yaml.dump(self.schema,default_flow_style=False)
        # re =yaml.dump_all([{k:v} for k,v in self.schema.items()],default_flow_style=False)
        # re =re.replace('---\n','',len(self.schema.keys()))
        return re

    def render(self):
        paths ={}
        for operation in self.operations:
            operation.render(paths,'app.apis.{model_name}.{tag}'.format(
                model_name=self.model_name,
                tag=operation.tag))

        self.schema =OrderDictEx({
            "swagger": "2.0",
            "info": {
                "title": self.title,
                "version": self.ver
            },
            "basePath":self.basepath ,
            "tags":[OrderDictEx({'name':tag.name,'description':tag.description}) for tag in self.tags ],
            "paths":paths,
            "definitions":{define.name.capitalize():define.render() for define in self.definitions}})

    def gen_aiohttp(self,app_struct):
        operations = self.operations
        tags = set([op.tag for op in operations])
        # handles = {}
        handles ={'routes.py':(genTemplate('aiohttp/routes',
                                           basepath =self.basepath,tags =tags,operations =operations),FileOp.OVERWRITE)}
        for tag in tags:
            handles['%s.py' % tag] =(genTemplate('aiohttp/handle',operations = filter(lambda op :op.tag ==tag ,operations)),FileOp.CREATE_NEW)
        app_struct['apis']=app_struct.get('apis',{})
        control_path ='%s_%s' % (self.name,self.ver)
        app_struct['apis'][control_path] =handles

        app_struct['swagger']=app_struct.get('swagger',{})
        app_struct['swagger']['%s.yml' % self.name]= (self.dump(),FileOp.OVERWRITE)


class SwaggerHandle(BaseGenerateHandle):
    swaggers=List[SwaggerProfile]
    def __init__(self, parser,service='app', hasxml =False,auths=None,lang=None,paginate =True):
        '''
        swagger handle 用于解析uml的内容转成swagger
        :param parser: 
        :param service: 工程的目录，default = app
        :param hasxml: 是否支持xml,会应用于path 的 consumers里
        :param auths: array|string 同时支持多种授权方式 [jwt|apikey]
        :param lang: string 多语言支持 [default]目前仅支持一种，default会将lang放在path的最前面。eg /a/b =>/{lang}/a/b 
        :param paginate: 对 get 且返回list 的operation,支持分页 query 中加入page,limit 
        '''
        super().__init__(parser)
        self.swaggers =[]
        self.hasxml =hasxml
        if type(auths)==str:
            self.auths =[auths]
        else:
            self.auths =auths
        self.lang =lang
        self.service =service
        self.paginate =paginate
        self.generate()

    def _parse(self,model):
        def parse_attr(attr,paramclass):
            _format = ''
            if type(attr.atype) in (str, UmlEnumeration):
                name, _format = get_sw_type_format(attr.atype if type(attr.atype) == str else 'integer')
            elif type(attr.atype) == UmlClass:
                name = attr.atype.name
            else:
                raise Exception('not support attr.atype:%s' % attr.atype)

            flags = attr.stereotype.split('/')
            return paramclass(attr.name,attr.title,required=('nq' in flags),
                        schema=SSParamSchema(name, format=_format,isarray=attr.isArray,isref=type(attr.atype)==UmlClass))


        def parse_in_param(attr):
            param =parse_attr(attr,SSInParam)
            flags = attr.stereotype.split('/')
            try:
                # cls =cls_map[[flag for flag in flags if flag in cls_map.keys()][0]]
                param.xin =[in_params_map.get(flag) for flag in flags if flag in in_params_map.keys()][0]
                return param
            except  :
                raise Exception('%s not define param in type:%s' % (attr.name, attr.stereotype))


        def parse_definition(uml_class):
            define =SSDefine(uml_class.name,uml_class.title)
            define.params =[parse_attr(attr,SSDefineParam) for attr in uml_class.attrs]
            return define
        # check stereotype is valid name-basepath
        name_basepath = model.stereotype.split('-')
        if len(name_basepath)<2:
            name_basepath =['swagger']+ name_basepath

        profile = SwaggerProfile(*name_basepath)

        singals = model.filterDeep(UmlSignal)
        profile.tags = [SStag(singal.name, singal.title) for singal in singals]

        for singal in singals:
            for operation in singal.operations:
                path_name = convert_pathname(operation.name)
                if self.lang =='default':
                    path_name ='/{lang}%s' %path_name

                ssop =SSoperation(operation.stereotype,path_name,singal.name,
                                  summary =operation.title,description=operation.description)
                profile.operations.append(ssop)

                # operation的第一个参数为 swagger 中的 params
                in_params = list(filter(lambda param: param.direction == 'in', operation.parameters))
                # in param 是UmlPrimitiveType ,取属性为params
                assert len(in_params) == 1 and type(in_params[0].atype) == UmlPrimitiveType
                in_param = in_params[0].atype

                ssop.in_params =[parse_in_param(attr) for attr in in_param.attrs]

                if self.lang == 'default':
                    #add path param
                    ssop.in_params.append(SSParam('lang','多语言',schema=SSParamSchema('string'),xin='path'))

                if self.auths:
                    if 'jwt' in self.auths:
                        ssop.in_params.append(SSParam('jwt', 'jwt token', schema=SSParamSchema('string'), xin='query',required=False))
                        ssop.in_params.append(
                            SSParam('jwt', 'jwt token', schema=SSParamSchema('string'), xin='header', required=False))

                    if 'apikey' in self.auths:
                        ssop.in_params.append(
                            SSParam('apikey', 'api key', schema=SSParamSchema('string'), xin='query', required=False))
                        ssop.in_params.append(
                            SSParam('apikey', 'api key', schema=SSParamSchema('string'), xin='header', required=False))

                re_params = list(filter(lambda param: param.direction == 'return', operation.parameters))
                # if len(re_params) == 0:
                #     ssop.re_params.append(SSParam('200','response message ok'))
                # else:
                assert len(re_params) >= 1 and type(re_params[0].atype) == UmlPrimitiveType
                if len(re_params[0].atype.attrs)==0:
                    ssop.re_params.append(SSResponseParam('default', 'response message ok'))
                else:
                    ssop.re_params =[parse_attr(attr,SSResponseParam) for attr in re_params[0].atype.attrs]
                    if self.paginate:
                        haspage =False
                        for param in ssop.re_params :
                            if ssop.method == 'get' and param.schema.isref and param.schema.isarray:
                                haspage=True
                                param.headers.append(SSDefineParam('x-total','所有记录笔数',schema=SSParamSchema('integer')))
                                param.headers.append(
                                    SSDefineParam('x-page', '第几页', schema=SSParamSchema('integer')))
                        if haspage:
                            ssop.in_params.append(SSInParam('page', '第几页', schema=SSParamSchema('integer'), xin='query'))
                            ssop.in_params.append(SSInParam('limit', '限制的记录笔数', schema=SSParamSchema('integer'), xin='query'))
        #done :write definitions
        uml_classes = model.filterDeep(UmlClass)
        profile.definitions =[parse_definition(uml_class) for uml_class in uml_classes]
        return profile

    def generate(self):
        models =self.root.search(lambda el: type(el)==UmlModel and el.name=='swagger')

        for model in models:
            self.swaggers.append(self._parse(model))

    def gen_aiohttps(self,app_struct):
        for swagger in self.swaggers:
            swagger.gen_aiohttp(app_struct)

        app_struct.update({'main.py':(genTemplate('aiohttp/main',swaggers =self.swaggers),FileOp.NO_OVERWRITE),
                           'config.py':(genTemplate('aiohttp/config'),FileOp.NO_OVERWRITE),
                           '__init__.py':('',FileOp.NO_OVERWRITE)})
        app_struct['apis'].update({'__init__.py':(genTemplate('aiohttp/apis_init',swaggers=self.swaggers),FileOp.NO_OVERWRITE)})


def parse_int(v, default):
    try:
        return int(v)
    except:
        return default


class SchemaType():
    name = str
    args = dict

    def __init__(self, name, **args):
        self.name = name
        self.args = args

    @classmethod
    def loads(cls, umltype):
        _type = umltype.lower()
        if _type.startswith('string'):
            return cls('String', length=parse_int(_type.split('string')[-1], 50))
        elif _type == 'boolean':
            return cls('Boolean')
        elif _type == 'datetime':
            return cls('DateTime')
        elif _type == 'time':
            return cls('Time')
        elif _type == 'double':
            return cls('Float')
        elif _type in ('int', 'integer'):
            return cls('Integer')
        elif _type == 'numeric':
            return cls('Numeric')
        elif _type == 'text':
            return cls('Text')
        elif _type == 'date':
            return cls('Date')
        elif _type == 'image':
            return cls('LargeBinary')
        else:
            raise Exception("umlTypeToSchemaType:not support (%s)" % (_type))


    def render(self):
        s = 'db.Column(db.%s' % self.name
        for k,v in self.args.items():
            s+=',%s = %s' % (k,v)
        return s + '%s)'

class FieldProfile:
    name =str
    description =str
    isArray =bool
    isUnique =bool
    isId =bool
    isReq =bool
    atype = SchemaType
    def __init__(self,name,description):
        self.name = name.lower()
        self.description = description
        self.isArray =False
        self.isId =False
        self.owner =None

    def render(self):
        s = ''
        if not self.isReq:
            s += ',nullable=False'
        if self.isUnique:
            s += ',unique=True'
        if self.isId:
            s+=',primary_key=True'
        s+=',comment="%s"' % self.description
        s = self.atype.render() % s
        return ['%s=%s' % (self.name ,s)]


class ModelProfile():
    description=str
    name =str
    tablename =str
    # fields = List[FieldProfile]
    as_association=bool
    def __init__(self,name,description,as_association=False):
        self.fields=[]
        self.name =name.capitalize()
        self.description =description
        self.tablename =self.name.lower()
        self.as_association =as_association


    @property
    def idfield(self):
        return list(filter(lambda field:field.isId,self.fields))[0]

    def add_field(self, field):
        field.owner = self
        self.fields.append(field)




def name_add_s(name,isarray):
    return (name + ('s' if isarray else '')).lower()

class AssociationField(FieldProfile):

    atype =ModelProfile

    association_type=AssociationType
    #b ->a 的关系
    # a的role name
    back_association_type =AssociationType


    secondary =ModelProfile
    def __init__(self,name,description):
        super().__init__(name,description)
        self.endAsLink =False
        # b ->a 的关系
        # a的role name
        self.back_name = None
        self.secondary =None

    @property
    def foreign_id(self):
        idfield =self.owner.idfield
        return ('%s_%s' % (self.name, idfield.name)).lower()

    def render_foreign_id(self):
        idfield = self.owner.idfield
        s =',db.ForeignKey("%s.%s")' % (self.name,idfield.name)
        if not self.isReq:
            s+=',nullable=False'
        s = idfield.atype.render() % s
        return '%s=%s' % (self.foreign_id ,s)

    def render_relationship(self):
        isarray =self.association_type == AssociationType.onetomany
        s ='%s =relationship("%s"' % (name_add_s(self.name,isarray),self.atype.name.capitalize())
        if self.secondary is not None:
            s +=',secondary = "%s"' % self.secondary.name
        else:
            if self.owner==self.atype and self.association_type in (AssociationType.manytoone,AssociationType.onetoone):
                s += ',remote_side = [%s]' % self.foreign_id
            s += ', uselist=%s' % str(self.association_type==AssociationType.onetomany)

            if self.back_name:
                if self.association_type==AssociationType.onetomany :
                    s +=',lazy = "dynamic", cascade = "all, delete-orphan"'

                s += ',back_populates="%s"' % name_add_s(self.back_name,self.back_association_type == AssociationType.onetomany)
        return s+')'
    def render(self):
        if self.association_type ==AssociationType.onetomany:
            return [self.render_relationship()]
        else:
            return [self.render_foreign_id(), self.render_relationship()]


class ModelHandle(BaseGenerateHandle):
    def __init__(self, parser, **args):
        super().__init__(parser,**args )
        self.dbmodels = {}
        self.generate()

    def _parse(self,model):
        def _parse_association_end(a,b,b_asstype=AssociationType.manytoone,b_isreq=False,b_alias=None,b_aslink=False):
            profile = self.dbmodels[a.name]
            field = AssociationField(b.name if (b_alias or '') == '' else b_alias,
                                     b.title)
            field.atype = self.dbmodels[b.name]
            field.association_type =b_asstype
            field.isReq =b_isreq
            field.endAsLink =b_aslink
            profile.add_field(field)
            return field

        def _parse_association_a(enda,endb,link=None):
            if endb.navigable or link is not None:
                asstype =AssociationType.onetomany if link else get_association_type(enda,endb)
                field =_parse_association_end(enda.reference,endb.reference,b_asstype=asstype,b_isreq = endb.isReq,b_alias=endb.name)
                field.secondary =link
                if enda.navigable and endb.navigable:
                    self.back_name = str(enda.name or enda.reference.name)
                    self.back_association_type =get_association_type(endb,enda) if link is None else AssociationType.onetomany

        def _parse_association(association,link=None):
            _parse_association_a(association.end1,association.end2,link)
            _parse_association_a(association.end2, association.end1,link)

        def _parse_association_link(link, association, as_link):
            def _parse_one_many(enda, link):
                field =_parse_association_end(enda.reference,link, b_asstype=AssociationType.onetomany, b_isreq=True)
                field.back_name =enda.name or enda.reference.name

            def _parse_many_one(link, enda):
                field =_parse_association_end(link, enda.reference, b_isreq=True,
                                       b_asstype=AssociationType.manytoone)
                if not as_link:
                    field.back_name = link.name

            _parse_many_one(link,association.end1)
            _parse_many_one(link, association.end2)


            if as_link:
                _parse_association(association, link=link)
            else: # as normal one ->many
                _parse_one_many(association.end1, link)
                _parse_one_many(association.end2, link)

        def _parse_attr_constraint(field,attr):
            field.isArray = attr.isArray
            field.isId = attr.isID
            field.isReq = field.isReq or attr.isID
            flags = attr.stereotype.split('/')
            field.isUnique = attr.isUnique or 'rep' in flags
            field.isReq = field.isReq or 'req' in flags

        def _parse_class_simple(uml_class):
            as_link =as_linkclass(uml_class)
            profile =ModelProfile(uml_class.name,uml_class.title,as_link)
            for attr in uml_class.attrs:
                if type(attr.atype ) in (str,UmlEnumeration):
                    field = FieldProfile(attr.name, attr.title)
                    field.atype = SchemaType.loads(attr.atype if type(attr)==str else 'integer')
                    _parse_attr_constraint(field, attr)
                    profile.add_field(field)

            #done: add auto id
            if uml_class.idattr is None and self.options.get('autoid',True):
                field =FieldProfile(self.options.get('id','id'),'auto id' )
                field.atype =SchemaType.loads(self.options.get('idtype','integer'))
                field.isReq =True
                field.isId =True
                profile.add_field(field)
            return profile

        def is_linkclass(uml_class):
            return type(uml_class.parent) == UmlClass
        def as_linkclass(uml_class):
            return is_linkclass(uml_class) and len(uml_class.attrs)<1
        uml_classes = model.filterDeep(UmlClass)
        # uml_classes =[uml_class for uml_class in uml_classes if type(uml_class.parent)!=UmlClass]
        self.dbmodels = {uml_class.name:_parse_class_simple(uml_class) for uml_class in uml_classes }

        for uml_class in uml_classes:
            if is_linkclass(uml_class):
                classlinks = uml_class.filter(UmlAssociationClassLink)
                for classlink in classlinks:
                    as_link = as_linkclass(uml_class)
                    # as_link = len(classlink.link.attrs) < 1
                    # profile = _parse_class_simple(classlink.link, as_link)
                    # self.dbmodels[profile.name] = profile
                    _parse_association_link(classlink.link, classlink.association, as_link=as_link)
            else:
                attrs = filter(lambda attr:type(attr.atype)==UmlClass ,uml_class.attrs )
                for attr in attrs:
                    asstype = AssociationType.onetomany if  attr.isArray else AssociationType.manytoone
                    field = _parse_association_end(uml_class, attr.atype, b_alias=attr.name, b_isreq=attr.isReq,b_asstype=asstype)
                    _parse_attr_constraint(field,attr)

                # done: handle associations
                associations = uml_class.filter(UmlAssociation)
                for association in associations:
                    _parse_association(association)


            # #done: handle linkclass
            # sub_classes =uml_class.filter(UmlClass)
            # for sub_class in sub_classes:
            #     classlinks = sub_class.filter(UmlAssociationClassLink)
            #     for classlink in classlinks:
            #         as_link = len(classlink.link.attrs)<1
            #         profile =_parse_class_simple(classlink.link,as_link)
            #         self.dbmodels[profile.name] =profile
            #         _parse_association_link(classlink.link,classlink.association,as_link =as_link)



    def generate(self):
        models = self.root.search(lambda el: type(el) == UmlModel and el.name == 'model')
        #model 只支持一个
        if len(models)>0:
            self._parse(models[0])



    def gen_aiohttp(self,app_struct):
        app_struct['models'] =app_struct.get('models',{})
        app_struct['models'].update({
            'model_base.py':(genTemplate('db_model_base',dbmodels = self.dbmodels.values(),modelclass='Base'),FileOp.OVERWRITE),
            'models.py':(genTemplate('db_model',dbmodels = self.dbmodels.values()),FileOp.CREATE_NEW)})
