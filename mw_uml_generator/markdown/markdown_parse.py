
import collections
from .md_render import InlineRenderer
from mistune import Markdown
import re

from ..swagger import *

def parse_text(token_text):
    txt = filter(lambda item:type(item)==str,token_text)
    return ''.join(txt).strip()
    # return "".join(list(filter(item['text'] for item in txt_token if item['type']=='text')))

class MdTable:
    def __init__(self,token_table):
        def parse_cell( token_cell):
            ls = []
            for item in token_cell['text']:
                if type(item) == str:
                    ls.append(item)
                elif type(item) == dict and item['type'] == 'inlinehtml' and item['text'] == '<br>':
                    ls.append('\r\n')
            return parse_text(ls)
        self.header=[parse_cell(tk_cell) for tk_cell in token_table['header'][0]]
        self.rows =[]
        for row in token_table['rows']:
            mdrow = [parse_cell(tk_cell) for tk_cell in row]
            while len(mdrow)<len(self.header):
                mdrow.append('')
            self.rows.append(mdrow)

class MdList:
    def __init__(self,token_list):
        self.items=[]
        for item in token_list['items']:
            if item['type']=='li':
                self.items.append(parse_text(item['text']))
    def to_json(self):
        re ={}
        for item in self.items:
            data =item.split(':')
            if len(data) == 2:
                re[data[0].strip()]=data[1].strip()
        return re



class JttParamType:
    def __init__(self,name,isArray,isTimestamp=False):
        self.name =name
        self.isArray = isArray
        self.fixLen =None
        self.isTimestamp = isTimestamp

    @classmethod
    def load(cls,type_text,directive=''):
        names =re.findall(r"\[(?P<name>.+)\…]", type_text)
        if len(names)>0:
            return JttParamType(names[0],True)

        names =re.findall(r"(?P<cc>.+)\[(?P<name>.+)\]", type_text)
        if len(names)>0:
            (name,fixlen)= names[0]
            param = JttParamType(name,False)
            param.fixLen = int(fixlen)
            return param

        names = re.findall(r"(?P<cc>.+)\[\]", type_text)
        if len(names)>0:
            return JttParamType(names[0], True)

        return JttParamType(type_text,False,type_text=='int64' and 'unix' in directive)

    def render(self):
        def swagger_param(name,fmt,minimum=None,maximum=None,isarray=False,fixlen=None,isref =False):
            p= {'name':name,
                'format':fmt,
                'isarray' :isarray,
                'isref' :isref}

            if fixlen:
                if isarray:
                    p['maxItems']=fixlen
                else:
                    (p['maxLength'], p['minLength']) = (fixlen, fixlen)

            if minimum:
                p['minimum']=minimum
            if maximum:
                p['maximum']=maximum
            return p

        name = self.name.lower()
        if name =='byte':
            return swagger_param('integer','int32',minimum=0,maximum=255,isarray=self.isArray,fixlen=self.fixLen)
        elif name =='word':
            return swagger_param('integer','int32',minimum=0,maximum=65535,isarray=self.isArray,fixlen=self.fixLen)
        elif name=='dword':
            return swagger_param('integer','int32',minimum=0,isarray=self.isArray,fixlen=self.fixLen)
        elif name =='int64' or name=='uint64':
            return swagger_param('integer','int64',isarray=self.isArray,fixlen=self.fixLen)
        elif name=='float':
            return swagger_param('number','float',isarray=self.isArray,fixlen=self.fixLen)
        elif name =='integer':
            return swagger_param('integer','int32',isarray=self.isArray,fixlen=self.fixLen)
        elif name =='boolean':
            return swagger_param('boolean',isarray=self.isArray,fixlen=self.fixLen)
        elif name =='string':
            return swagger_param('string','',isarray=self.isArray,fixlen=self.fixLen)
        elif name=='dict':
            return swagger_param('PlaceHolder','',isarray=self.isArray,fixlen=self.fixLen,isref =True)

        else:
            return swagger_param(self.name,'',isarray=self.isArray,fixlen=self.fixLen,isref =True)


RowParam = collections.namedtuple('RowParam', 'name type desc directive')


class TokenNode():
    def __init__(self,level,text):
        self.level =level
        self.text =text
        self.contents=[]
        self.children =[]
    def deep_filter(self,condition):
        re =[]
        if condition(self):
            re.append(self)
        for child in self.children:
           re += child.deep_filter(condition)
        return re

    def find_firstchild(self,condition):
        for child in self.children:
            if condition(child):
                return child

    def find_first(self,level,txtlike ):
        nodes =self.deep_filter(lambda node:node.level ==level and txtlike in node.text)
        if len(nodes)>0:
            return nodes[0]

    def find_tokens(self,token_type):
        return list(filter(lambda token: token['type'] == token_type, self.contents))

    def find_first_token(self,token_type):
        re = self.find_tokens(token_type)
        if len(re)>0:
            return re[0]

class MdTemplateParser():
    root = TokenNode
    def __init__(self,swagger=None):
        self.root =None
        if swagger:
            self.swagger =swagger
        else:
            self.swagger =SwaggerProfile('swagger','','')

    def group_tokens(self,valid_header,tokens):
        groups =[]
        node =None
        for token in tokens:
            header = valid_header(token)
            if header:
                node = TokenNode(*header)
                groups.append(node)
            else:
                if node is not None:
                    node.contents.append(token)
        return groups

    def groupby_header(self,tokens,level):
        def parse_header(level):
            def check_header(token):
                if token['type'] == 'header' and token['level'] ==level:
                    return token['level'],parse_text(token['text'])
            return check_header

        groups = self.group_tokens(parse_header(level),tokens)
        for group in groups :
            if level <= 5:
                group.children = self.groupby_header(group.contents,level+1)

        return groups

    def parse_config(self):
        if self.root is None:
            return

        node =self.root.find_first(2,'配置')
        assert node is not None, '文档必需有配置项'
        config =node.find_first_token('list')
        assert config is not None , '文档必需有配置内容和basePath'
        cf = MdList(config).to_json()
        assert 'basePath' in cf.keys(),'文档必需有配置basePath'

        self.swagger.basepath =cf['basePath']
        self.swagger.title = self.root.text

    def table_row_to_param(self,row,paramCls,**args):
        r = RowParam(*row)
        directives = parse_directive(r.directive)
        directives['xin'] = directives.get('xin', 'body')
        directives['required'] = directives.get('required', False) or directives['xin'] == 'path'
        directives.update(**args)
        jtt_type = JttParamType.load(r.type)
        if paramCls ==SSInParam:
            return SSInParam(r.name,r.desc,required =directives['required'],
                      schema=SSParamSchema(**jtt_type.render()) ,
                      xin = directives['xin'])
        else:
            return paramCls(r.name, r.desc, required=directives['required'],
                      schema=SSParamSchema(**jtt_type.render()),
                      )

    def parse_define(self):
        node =self.root.find_first(2,'定义')
        if node is None:
            return

        for item in node.children:
            txt = item.text.split(' ')[-1]
            de = SSDefine(*(split_title(txt)))
            _tb = item.find_first_token('table')
            assert _tb is not None,'未设定%s定义的参数' % txt
            tb = MdTable(_tb)
            de.params = [self.table_row_to_param(row,SSDefineParam) for row in tb.rows]

            token = item.find_first_token('list')
            if token is not None:
                ls = MdList(token)
                for item in ls.items:
                    name, directive = split_title(item)
                    if directive == 'allof':
                        de.allOf.append(name)
            self.swagger.definitions.append(de)


    def parse_operations(self):
        node = self.root.find_first(2, '协议')
        if node is None:
            return
        for category in node.children:
            swtag = SStag(*split_title(category.text))
            self.swagger.tags.append(swtag)
            # 对每个node 下，是每个方法的定义
            for item in category.children:
                token = item.contents[0]
                assert(token['type']=='code')
                try:
                    [method,pathname] =list( filter(lambda txt: txt.strip()!='', parse_text(token['text']).split(' ')))
                except Exception as e:
                    raise Exception('%s不合法,%s' % (parse_text(token['text']),str(e)))

                operation = SSoperation(method.lower(), pathname, swtag.name, item.text)
                self.swagger.operations.append(operation)

                desc = item.find_firstchild(lambda node: '描述' in node.text)
                if desc and len(desc.contents) > 0:
                    operation.description = parse_text(desc.contents[0]['text'])

                inparam = item.find_firstchild(lambda node: '请求参数' in node.text)
                if inparam:
                    _tb = item.find_first_token('table')
                    if _tb is not None:
                        tb = MdTable(_tb)
                        operation.in_params = [self.table_row_to_param(row,SSInParam) for row in tb.rows if row[0].strip()!='']


                outparam = item.find_firstchild(lambda node: '返回结果' in node.text)
                if outparam:
                    tbs = list(filter(lambda token: token['type'] == 'table', outparam.contents))
                    for _tb in tbs:
                        tb = MdTable(_tb)
                        r = RowParam(*tb.rows[0])

                        param = self.table_row_to_param(r,SSResponseParam)
                        param.headers =[self.table_row_to_param(row,SSInParam,xin='header') for row in tb.rows[1:]]

                        operation.re_params.append(param)

    def parse_template(self):
        node = self.root.find_first(2, '模版')
        if node is None:
            return
        template = node.find_first(3,'path参数')
        if template is None:
            return
        _tb = template.find_first_token('table')
        if _tb:
            tb =MdTable(_tb)
            for op in self.swagger.operations:
                for row in tb.rows:
                    if '{%s}' % row[0] in op.pathname:
                        op.in_params.append(self.table_row_to_param(row,SSInParam))

    def parse(self,filename):
        with open(filename) as f:
            text =f.read()
        markdown = Markdown(renderer=InlineRenderer())
        tokens = markdown(text)
        #对tokens进行分组后parser
        groups = self.groupby_header(tokens,1)
        assert len(groups)>0,'文档格式错误'
        self.root =groups[0]

        #查找配置
        self.parse_config()
        #对定义部份单独解析
        self.parse_define()

        #对协议部分单独解析
        self.parse_operations()

        self.parse_template()
        return self.swagger



