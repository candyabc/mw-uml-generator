from enum import Enum
import json

# class AutoID(Enum):
#     NONE ='none'
#     INT = 'int'
#     STR = 'str'

########aggregation########
AGGREGATION_NONE ="none"
AGGREGATION_SHARED ="shared"
AGGREGATION_COMPOSITE ="composite"

class Aggregation(Enum):
    NONE ='none'
    SHARED='shared'
    COMPOSITE='composite'

UML_TYPE ='_type'
UML_ID='_id'
UML_PARENT ='_parent'
UML_OWNED_ELEMENTS='ownedElements'
UML_ATTR_TYPE='type'
UML_REF ='$ref'

UML_INNER_PROPS={UML_TYPE: 'xtype',
                   UML_ID: 'id',
                   UML_OWNED_ELEMENTS:'children',
                   'attributes':'attrs',
                   UML_ATTR_TYPE:'atype'
                   }

class Singleton(type):
    def __new__(cls, name,bases,attrs):
        attrs["_instance"] = None
        return super(Singleton,cls).__new__(cls,name,bases,attrs)


    def __call__(self, *args, **kwargs):
        if self._instance is None:
            self._instance = super(Singleton,self).__call__(*args, **kwargs)
        return self._instance

class UmlParserBaseFactory():
    defaultClass =None
    def __init__(self):
        self._classMapping={}
    def addClass(self,elClass,eltype=None):
        key =elClass.__name__ if eltype is None else eltype
        self._classMapping[key.lower()]=elClass

    def getClass(self,xtype):
        return self._classMapping.get(xtype.lower()) or self.defaultClass

    def create(self,parser,xtype,data):
        elClass =self.getClass(xtype)
        if elClass !=None:
            el =elClass()
            el.load(parser, data)

            return el

class UmlParserFactory(UmlParserBaseFactory,metaclass=Singleton):
    defaultClass = None


class ElRegistor(type):
    '''用于对factory 的_classMappings的mdj文件中的element._type与class对应
    类名命名规则为xx_[_type] 或 [_type]
    '''
    _factory = UmlParserFactory()
    def __new__(cls, name, bases, attrs):
        new_cls = super(ElRegistor, cls).__new__(cls, name, bases, attrs)
        cls._factory.addClass(new_cls,name.split('_')[-1].lower())
        return new_cls

class UmlDict():
    def __init__(self):
        self._elements={}
    def add(self,el):
        self._elements[el.id]=el
    def get(self,id):
        return self._elements.get(id)
    def getRef(self,data):
        if not UML_REF in data.keys():
            raise Exception('data is not a ref')
        return self.get(data[UML_REF])
    @property
    def elements(self):
        return list(self._elements.values())

    def filter(self,elClasses):
        '''
                以类别 filter 数据
                :param elClasses:  class of umlelement or [class of umlelement]
                :return: []
                '''

        # if hasSupers:
        #     return [el for el in self._elements.values() if isinstance(el,classType)]
        # else:
        if type(elClasses)!=list:
            elClasses =[elClasses]
        return [el for el in self._elements.values() if type(el)in elClasses]

    def search(self,searchFunc):
        return [el for el in self._elements.values() if searchFunc(el)]

    def filterDeep(self, elClass):
        '''
        用于从这一层一直找到最后，找出所有class 相同的element
        :param elClass: 
        :return: 
        '''
        def _filter(parent, elClass):
            found = parent.filter(elClass)
            folders = parent.search(lambda el : hasattr(el,'children') and len(el.children)>0)
            # folders = parent.filter(MoUmlFolder, True)
            # print(folders)
            for folder in folders:
                found += _filter(folder, elClass)
            return found

        return _filter(self, elClass)

def get_default_value(typ):
    if typ==str:
        return ''
    elif typ==int:
        return 0
    elif typ ==bool:
        return False
    elif typ==list:
        return []
    elif typ ==dict:
        return {}
    else:
        raise Exception('get_default_value not support type:%s' % typ)

class UmlElement(UmlDict,metaclass=ElRegistor):
    stereotype= str
    id = str
    name =str
    documentation = str
    description = str
    def __init__(self):
        super().__init__()
        self._init_default_value()

        # self.stereotype =""
        # self.id =""
        # self.name =""
        # self.documentation =""
        # self.description =""
    def _init_default_value(self):

        '''
        用来设定默认值
        :return: 
        '''
        import inspect
        props=inspect.getmembers(self.__class__,inspect._is_type)

        for prop,v in props:
            if (not prop.startswith('_')) :
                try:
                    setattr(self,prop,get_default_value(v))
                except Exception as e:
                    raise Exception('%s ,prop:%s,%s' % (self.name,prop,str(e)))

    def _innerPropName(self,prop):
        return  UML_INNER_PROPS.get(prop) or prop

    @property
    def children(self):
        return self.elements

    def load(self,parser,args):
        if args ==None:
            return
        for prop in args:
            innerPropName = self._innerPropName(prop)
            # if hasattr(self,innerProp):
            value =items = args[prop]

            if type(value) == list:# 如果属性是列表
                els =list(filter(lambda item :item!=None, [parser.createEl(item) for item in items ]))
                if prop==UML_OWNED_ELEMENTS:
                    for el in els:
                        self.add(el)
                else:
                    setattr(self,innerPropName,els)
            elif type(value) ==dict: #属性是dict,则是单个的element
                if parser.isElement(value):
                    setattr(self,innerPropName,parser.createEl(value))
                else:
                    setattr(self,innerPropName,value)
            else:
                setattr(self,innerPropName,value)

    def extraLoad(self,parser):
        # LOAD PARENT
        if hasattr(self,UML_PARENT):
            self.parent =parser.getRef(getattr(self,UML_PARENT))

        # LOAD UML_ATTR_TYPE
        if hasattr(self,'atype') :
            atype = getattr(self,'atype')
            if type(atype)==dict:
                setattr(self,'atype',parser.getRef(atype))

    def __repr__(self):
        return "%s:(name:%s,children:%s)\r\n" % (self.xtype,self.name,repr(self.children) if len(self.children)>0 else "")


class UmlParser(UmlDict):
    def __init__(self, elementFactory=None):
        super().__init__()
        self.elementFactory =elementFactory if elementFactory else UmlParserFactory()
        self.root = None

    def isElement(self, data): # data 是否是合法的umlelement
        return data.get(UML_TYPE) != None

    def createEl(self, data):
        if not self.isElement(data):
            raise Exception('can not create element,data is not a umlelement')
        xtype = data[UML_TYPE]
        el = self.elementFactory.create(self, xtype, data)
        if el != None:
            self.add(el)
        return el

    def load(self, filename):
        with open(filename, encoding='utf-8') as f:
            data = json.loads(f.read())

            self.root =self.createEl(data)
            #为所有的element set parent 和装入关联数据
            for element in self.elements:
                element.extraLoad(self)

