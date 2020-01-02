
from ..uml_parser import *
from ..swagger import *
import re
from ..markdown import MdTemplateParser

from typing import (List)
from ..template import genTemplate
from ..fileutils import FileOp

SS_FILE_IMG ='img'
SS_FILE_PDF = 'pdf'
SS_FILE_EXCEL = 'excel'

def get_sw_type_format(atype):
    '''
    根据 model里的类型转成 swagger 的类型及 format格式
    :param atype: 
    :return: 
    '''
    atype = atype.lower().strip()
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
        # print(type)
        raise Exception('swagger type not support :%s' % type)
        # assert False, 'swagger type not support :%s' % type
        # return atype, ''


def convert_pathname(pathname):
    '''
    将pathname转换成swagger中标准的path，如 {company_id}_task_{id} 转换为{company_id}/task/{id}，注意{}里的_不做转换
    :param pathname: 
    :return: 
    '''
    params = re.findall('{\w+}', pathname)
    name = re.sub('{\w+}', '%s', pathname).replace('_', '/')
    return '/' + name % tuple(params)

class EnumProfile():
    literals =List[str]
    def __init__(self,name,description):
        self.name =name
        self.description = description
        self.literals =[]

class BaseGenerateHandle():
    def __init__(self, parser):
        self.parser = parser
        self.root = self.parser.root
        self.generate()

    def parse_enums(self,model):
        uml_enums = model.filterDeep(UmlEnumeration)
        return [self.parse_enum(uml_enum) for uml_enum in uml_enums]


    def parse_enum(self,uml_enum):
        enum_profile = EnumProfile(uml_enum.name, uml_enum.title)
        enum_profile.literals = [(literal.name, literal.title) for literal in uml_enum.literals]
        return enum_profile
    def generate(self):
        pass

class AioSwaggerProfile(SwaggerProfile):
    def gen_aiohttp(self, app_struct):
        operations = self.operations
        tags = set([op.tag for op in operations])
        # handles = {}
        handles = {'routes.py': (genTemplate('aiohttp/routes',
                                             basepath=self.basepath, tags=tags, operations=operations),
                                 FileOp.OVERWRITE)}
        for tag in tags:
            handles['%s.py' % tag] = (
            genTemplate('aiohttp/handle', operations=filter(lambda op: op.tag == tag, operations)), FileOp.CREATE_NEW)
        app_struct['apis'] = app_struct.get('apis', {})
        control_path = '%s_%s' % (self.name, self.ver)
        app_struct['apis'][control_path] = handles

        app_struct['swagger'] = app_struct.get('swagger', {})
        app_struct['swagger']['%s.yml' % self.name] = (self.dump(), FileOp.OVERWRITE)


class SwaggerHandle(BaseGenerateHandle):
    swaggers = List[SwaggerProfile]

    def __init__(self, parser, service='app', hasxml=False, auths=None, lang=None, paginate=True):
        '''
        swagger handle 用于解析uml的内容转成swagger
        :param parser: 
        :param service: 工程的目录，default = app
        :param hasxml: 是否支持xml,会应用于path 的 consumers里
        :param auths: array|string 同时支持多种授权方式 [jwt|apikey]
        :param lang: string 多语言支持 [default]目前仅支持一种，default会将lang放在path的最前面。eg /a/b =>/{lang}/a/b 
        :param paginate: 对 get 且返回list 的operation,支持分页 query 中加入page,limit 
        '''

        self.swaggers = []
        self.enum_profiles =[]
        self.hasxml = hasxml
        if type(auths) == str:
            self.auths = [auths]
        else:
            self.auths = auths
        self.lang = lang
        self.service = service
        self.paginate = paginate
        super().__init__(parser)

    def _parse(self, model):
        def parse_attr(attr, paramclass):
            _format = ''
            if type(attr.atype) == str :
                try:
                    name, _format = get_sw_type_format(attr.atype )
                except Exception as e :
                    raise Exception('attr %s get_sw_type_format error :%s' %(attr,str(e)))
            elif type(attr.atype)==UmlEnumeration:
                name ='string'

            elif type(attr.atype) == UmlClass:
                name = attr.atype.name
            else:
                raise Exception('not support attr.atype:%s' % attr.atype)

            flags = attr.stereotype.split('/')
            return paramclass(attr.name, attr.title, required=('nq' in flags),
                              schema=SSParamSchema(name, format=_format, isarray=attr.isArray,
                                                   isref=type(attr.atype) == UmlClass,
                                                   enum_define=self.parse_enum(attr.atype) if type(attr.atype)==UmlEnumeration else None),
                                                   file_types = attr.stereotype.split('/') if name =='file' else [])

        def parse_in_param(attr):
            param = parse_attr(attr, SSInParam)
            flags = attr.stereotype.split('/')
            try:
                # cls =cls_map[[flag for flag in flags if flag in cls_map.keys()][0]]
                param.xin = [in_params_map.get(flag) for flag in flags if flag in in_params_map.keys()][0]
                return param
            except:
                raise Exception('%s not define param in type:%s' % (attr.name, attr.stereotype))

        def parse_definition(uml_class):
            define = SSDefine(uml_class.name, uml_class.title)
            define.params = [parse_attr(attr, SSDefineParam) for attr in uml_class.attrs]
            return define

        # check stereotype is valid name-basepath
        name_basepath = model.stereotype.split('-')
        if len(name_basepath) < 2:
            name_basepath = ['swagger'] + name_basepath

        profile = AioSwaggerProfile(*name_basepath)
        if self.hasxml:
            profile.produces.append('application/xml')
            profile.consumes.append('application/xml')
        singals = model.filterDeep(UmlSignal)
        profile.tags = [SStag(singal.name, singal.title) for singal in singals]

        for singal in singals:
            for operation in singal.operations:
                path_name = convert_pathname(operation.name)
                if self.lang == 'default':
                    path_name = '/{lang}%s' % path_name

                ssop = SSoperation(operation.stereotype, path_name, singal.name,
                                   summary=operation.title, description=operation.description)
                profile.operations.append(ssop)

                # operation的第一个参数为 swagger 中的 params
                in_params = list(filter(lambda param: param.direction == 'in', operation.parameters))
                # in param 是UmlPrimitiveType ,取属性为params
                assert len(in_params) == 1 and type(in_params[0].atype) == UmlPrimitiveType
                in_param = in_params[0].atype

                ssop.in_params = [parse_in_param(attr) for attr in in_param.attrs]

                if self.lang == 'default':
                    # add path param
                    ssop.in_params.append(SSInParam('lang', '多语言', schema=SSParamSchema('string'), xin='path'))

                if self.auths:
                    if 'jwt' in self.auths:
                        ssop.in_params.append(
                            SSInParam('jwt', 'jwt token', schema=SSParamSchema('string'), xin='query', required=False))
                        # ssop.in_params.append(
                        #     SSInParam('jwt', 'jwt token', schema=SSParamSchema('string'), xin='header', required=False))

                    if 'apikey' in self.auths:
                        ssop.in_params.append(
                            SSInParam('apikey', 'api key', schema=SSParamSchema('string'), xin='query', required=False))
                        # ssop.in_params.append(
                        #     SSInParam('apikey', 'api key', schema=SSParamSchema('string'), xin='header', required=False))

                re_params = list(filter(lambda param: param.direction == 'return', operation.parameters))
                # if len(re_params) == 0:
                #     ssop.re_params.append(SSParam('200','response message ok'))
                # else:
                assert len(re_params) >= 1 and type(re_params[0].atype) == UmlPrimitiveType
                if len(re_params[0].atype.attrs) == 0:
                    ssop.re_params.append(SSResponseParam('default', 'response message ok'))
                else:
                    ssop.re_params = [parse_attr(attr, SSResponseParam) for attr in re_params[0].atype.attrs]
                    if self.paginate:
                        haspage = False
                        for param in ssop.re_params:
                            if ssop.method == 'get' and param.schema.isref and param.schema.isarray:
                                haspage = True
                                param.headers.append(
                                    SSDefineParam('x-total', '所有记录笔数', schema=SSParamSchema('integer')))
                                param.headers.append(
                                    SSDefineParam('x-page', '第几页', schema=SSParamSchema('integer')))
                        if haspage:
                            ssop.in_params.append(
                                SSInParam('page', '第几页', schema=SSParamSchema('integer'), xin='query'))
                            ssop.in_params.append(
                                SSInParam('limit', '限制的记录笔数', schema=SSParamSchema('integer'), xin='query'))
        # done :write definitions
        uml_classes = model.filterDeep(UmlClass)
        profile.definitions = [parse_definition(uml_class) for uml_class in uml_classes]
        return profile
    def md2swagger(self,filename,name):
        swagger = AioSwaggerProfile(name,'')
        parser =MdTemplateParser(swagger)
        parser.parse(filename)
        self.swaggers.append(swagger)

    def generate(self):
        models = self.root.search(lambda el: type(el) == UmlModel and el.name == 'swagger')

        for model in models:
            self.swaggers.append(self._parse(model))

    def gen_aiohttps(self, app_struct):
        for swagger in self.swaggers:
            swagger.gen_aiohttp(app_struct)

        app_struct.update({'main.py': (genTemplate('aiohttp/main', swaggers=self.swaggers), FileOp.NO_OVERWRITE),
                           'config.py': (genTemplate('aiohttp/config'), FileOp.NO_OVERWRITE),
                           '__init__.py': ('', FileOp.NO_OVERWRITE)})
        app_struct['apis'].update(
            {'__init__.py': (genTemplate('aiohttp/apis_init', swaggers=self.swaggers), FileOp.NO_OVERWRITE)})


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
        elif _type in [ 'double','float']:
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
        args = []
        for k, v in self.args.items():
            args.append('%s=%s' % (k, v))
        else:
            if len(args) > 0:
                s += '(%s)' % ','.join(args)
                # s+=',%s = %s' % (k,v)
        return s + '%s)'


class FieldProfile:
    name = str
    description = str
    isArray = bool
    isUnique = bool
    isId = bool
    isReq = bool
    atype = SchemaType

    def __init__(self, name, description):
        self.name = name.lower()
        self.description = description
        self.isArray = False
        self.isId = False
        self.owner = None

    def render(self):
        s = ''
        if not self.isReq:
            s += ',nullable=False'
        if self.isUnique:
            s += ',unique=True'
        if self.isId:
            s += ',primary_key=True'
        s += ',comment="%s"' % self.description
        s = self.atype.render() % s
        return ['%s=%s' % (self.name, s)]


class ModelProfile():
    description = str
    name = str
    tablename = str
    # fields = List[FieldProfile]
    as_association = bool

    def __init__(self, name, description, as_association=False):
        self.fields = []
        self.name = name.capitalize()
        self.description = description
        self.tablename = self.name.lower()
        self.as_association = as_association

    @property
    def idfield(self)->FieldProfile:
        return list(filter(lambda field: field.isId, self.fields))[0]

    def add_field(self, field):
        field.owner = self
        self.fields.append(field)

    def render_fields(self):
        re =[]
        for field in self.fields:
            re.extend(field.render())

        return re

    def render_as_columns(self):
        re =[]
        for field in self.fields:
            schema =field.render()[0]
            index = schema.find('=')
            name =schema[:index]
            schema =schema[index+1:]

            findstr ='db.Column('
            schema=schema.replace(findstr,findstr +'"%s",' % name)
            re.append(schema)

        return re





def name_add_s(name, isarray):
    return (name + ('s' if isarray else '')).lower()


class AssociationField(FieldProfile):
    atype = ModelProfile

    association_type = AssociationType
    # b ->a 的关系
    # a的role name
    back_association_type = AssociationType

    secondary = ModelProfile

    def __init__(self, name, description,id_connector):
        super().__init__(name, description)
        self.endAsLink = False
        # b ->a 的关系
        # a的role name
        self.back_name = None
        self.secondary = None
        self.id_connector =id_connector

    def foreign_idfield(self):
        return self.atype.idfield

    @property
    def foreign_id(self):
        return ('%s%s%s' % (self.name,self.id_connector, self.foreign_idfield().name)).lower()

    def render_foreign_id(self):
        idfield = self.foreign_idfield()
        s = ',db.ForeignKey("%s.%s")' % (self.name, idfield.name)
        if not self.isReq:
            s += ',nullable=False'
        s = idfield.atype.render() % s
        return '%s=%s' % (self.foreign_id, s)

    def render_relationship(self):
        isarray = self.association_type == AssociationType.onetomany
        s = '%s =relationship("%s"' % (name_add_s(self.name, isarray), self.atype.name.capitalize())
        if self.secondary is not None:
            s += ',secondary = "%s"' % self.secondary.name.lower()
        else:
            if self.owner == self.atype and self.association_type in (
            AssociationType.manytoone, AssociationType.onetoone):
                s += ',remote_side = [%s]' % self.foreign_id
            s += ', uselist=%s' % str(self.association_type == AssociationType.onetomany)

            if self.back_name:
                if self.association_type == AssociationType.onetomany:
                    s += ',lazy = "dynamic", cascade = "all, delete-orphan"'

                s += ',back_populates="%s"' % name_add_s(self.back_name,
                                                         self.back_association_type == AssociationType.onetomany)
        return s + ')'

    def render(self):
        if self.association_type == AssociationType.onetomany:
            return [self.render_relationship()]
        else:
            return [self.render_foreign_id(), self.render_relationship()]


class ModelHandle(BaseGenerateHandle):
    def __init__(self, parser,autoid=True,id_name='id',id_type='integer',id_connector='_'):
        self.dbmodels = {}
        self.enum_profiles =[]
        self.autoid = autoid
        self.id_name = id_name
        self.id_type = id_type
        self.id_connector = id_connector

        super().__init__(parser)
    def _parse(self, model):

        def _parse_association_end(a, b, b_asstype=AssociationType.manytoone, b_isreq=False, b_alias=None,
                                   b_aslink=False):
            profile = self.dbmodels[a.name]
            field = AssociationField(b.name if (b_alias or '') == '' else b_alias,
                                     b.title,self.id_connector)
            field.atype = self.dbmodels[b.name]
            field.association_type = b_asstype
            field.isReq = b_isreq
            field.endAsLink = b_aslink
            profile.add_field(field)
            return field

        def _parse_association_a(enda, endb, link=None):
            if endb.navigable or link is not None:
                asstype = AssociationType.onetomany if link else get_association_type(enda, endb)
                field = _parse_association_end(enda.reference, endb.reference, b_asstype=asstype, b_isreq=endb.isReq,
                                               b_alias=endb.name)
                field.secondary = link
                if enda.navigable and endb.navigable:
                    self.back_name = str(enda.name or enda.reference.name)
                    self.back_association_type = get_association_type(endb,
                                                                      enda) if link is None else AssociationType.onetomany

        def _parse_association(association, link=None):
            _parse_association_a(association.end1, association.end2, link)
            _parse_association_a(association.end2, association.end1, link)

        def _parse_association_link(link, association, as_link):
            def _parse_one_many(enda, link):
                field = _parse_association_end(enda.reference, link, b_asstype=AssociationType.onetomany, b_isreq=True)
                field.back_name = enda.name or enda.reference.name

            def _parse_many_one(link, enda):
                field = _parse_association_end(link, enda.reference, b_isreq=True,
                                               b_asstype=AssociationType.manytoone)
                if not as_link:
                    field.back_name = link.name

            _parse_many_one(link, association.end1)
            _parse_many_one(link, association.end2)

            if as_link:
                _parse_association(association, link=link)
            else:  # as normal one ->many
                _parse_one_many(association.end1, link)
                _parse_one_many(association.end2, link)

        def _parse_attr_constraint(field, attr):
            field.isArray = attr.isArray
            field.isId = attr.isID
            field.isReq = field.isReq or attr.isID
            flags = attr.stereotype.split('/')
            field.isUnique = attr.isUnique or 'rep' in flags
            field.isReq = field.isReq or 'req' in flags

        def _parse_class_simple(uml_class):
            as_link = as_linkclass(uml_class)
            profile = ModelProfile(uml_class.name, uml_class.title, as_link)
            for attr in uml_class.attrs:
                if type(attr.atype) in (str, UmlEnumeration):
                    field = FieldProfile(attr.name, attr.title)
                    field.atype = SchemaType.loads(attr.atype if type(attr.atype) == str else 'integer')
                    _parse_attr_constraint(field, attr)
                    profile.add_field(field)

            # done: add auto id
            if uml_class.idattr is None and self.autoid:
                field = FieldProfile(self.id_name,'auto id')
                field.atype = SchemaType.loads(self.id_type)
                field.isReq = True
                field.isId = True
                profile.add_field(field)
            return profile

        def is_linkclass(uml_class):
            return type(uml_class.parent) == UmlClass

        def as_linkclass(uml_class):
            return is_linkclass(uml_class) and len(uml_class.attrs) < 1

        self.enum_profiles = self.parse_enums(model)
        uml_classes = model.filterDeep(UmlClass)
        # uml_classes =[uml_class for uml_class in uml_classes if type(uml_class.parent)!=UmlClass]
        self.dbmodels = {uml_class.name: _parse_class_simple(uml_class) for uml_class in uml_classes}

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
                attrs = filter(lambda attr: type(attr.atype) == UmlClass, uml_class.attrs)
                for attr in attrs:
                    asstype = AssociationType.onetomany if attr.isArray else AssociationType.manytoone
                    field = _parse_association_end(uml_class, attr.atype, b_alias=attr.name, b_isreq=attr.isReq,
                                                   b_asstype=asstype)
                    _parse_attr_constraint(field, attr)

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
        # model 只支持一个
        if len(models) > 0:
            self._parse(models[0])

    def gen_aiohttp(self, app_struct):
        app_struct['models'] = app_struct.get('models', {})
        app_struct['models'].update({
            'model_base.py': (
            genTemplate('db_model_base', dbmodels=self.dbmodels.values(),
                        enum_profiles = self.enum_profiles, modelclass='Base'), FileOp.OVERWRITE),
            'models.py': (genTemplate('db_model', dbmodels=self.dbmodels.values()), FileOp.CREATE_NEW)})

    def gen_table_define(self,app_struct):
        app_struct['models'] = app_struct.get('models', {})
        app_struct['models'].update({'models.py':(genTemplate('db_table_define', dbmodels=self.dbmodels.values(),
                        enum_profiles = self.enum_profiles), FileOp.OVERWRITE)})
