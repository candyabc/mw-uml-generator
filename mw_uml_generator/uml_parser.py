import re
from enum import Enum

from .base_umlparser import UmlElement,UmlParser

def split_document(document):
    # 以 ----------- 来分隔title,description
   l= re.split('-+',document or '')
   return l[0].strip(),l[1].strip() if len(l)>=2 else ""

class MoUmlElement(UmlElement):
    def extraLoad(self,parser):
        super().extraLoad(parser)
        self.title,self.description =split_document(self.documentation)

class Uml_Project(MoUmlElement):
    '''由于staruml中project 的_type是project ,所以加_ 用于factory 找到'''
    pass

class UmlObject(MoUmlElement):
    slots = list
    def to_dict(self):
        re ={}
        for slot in self.slots:
            v =slot.value
            if v.atype =='integer':
                v =int(v)
            elif v.atype =='boolean':
                v=bool(v)
            re[slot.name]= v
        return re

class UmlSlot(MoUmlElement):
    value=str
    atype = str


class UmlAttrBase(MoUmlElement):
    isUnique=bool
    atype=str #type could be str or dict
    isID =bool
    aggregation =str
    multiplicity=str
    defaultValue =str
    @property
    def isReq(self):
        return self.multiplicity in ('1','1..*')

    @property
    def isArray(self):
        return self.multiplicity in ('0..*','1..*')


class UmlParameter(UmlAttrBase):
    direction ='in'


class UmlAttribute(UmlAttrBase):
    pass


class UmlClass(MoUmlElement):
    operations = list
    attrs = list

    @property
    def idattr(self):
        for attr in self.attrs:
            if attr.isID:
                return attr
        else:
            return None

    def get_attr_by_name(self, name):
        for attr in self.attrs:
            if attr.name ==name:
                return attr
    def has_attr(self,name):
        return len(list(filter(lambda attr:attr.name ==name ,self.attrs )))>0

    def do_generalize(self):
        # print('generalize %s' % self.name)
        generalizations = self.filter(UMLGeneralization)
        for generalization in generalizations:
            if not generalization.is_generalize:
                generalization.ancestor.do_generalize()
                for attr in generalization.ancestor.attrs:
                    if not self.has_attr(attr.name):
                        self.attrs.append(attr)

                generalization.set_generalize()


class UmlPackage(MoUmlElement):
    pass

class UmlModel(UmlPackage):
    pass

class UmlEnumeration(MoUmlElement):
    literals=list


class UmlEnumerationLiteral(MoUmlElement):
    pass

class UmlAssociationClassLink(MoUmlElement):
    classSide =dict
    associationSide=dict
    def extraLoad(self,parser):
        super().extraLoad(parser)
        self.link =parser.getRef(self.classSide)
        self.association =parser.getRef(self.associationSide)


class UmlAssociationEnd(MoUmlElement):
    navigable = bool
    aggregation =str
    multiplicity = str
    reference = dict
    def __init__(self):
        super().__init__()
        #modified by candy,v3.1版后staruml中navigable默认为true
        self.navigable=True

    def extraLoad(self,parser):
        super().extraLoad(parser)
        self.reference =parser.getRef(self.reference)


    @property
    def isArray(self):
        return self.multiplicity in ['0..*', '1..*']


    @property
    def isReq(self):
        return self.multiplicity in ('1', '1..*')

    @property
    def isRep(self):
        return self.multiplicity in ('1', '1..*')


class AssociationType(Enum):
    onetoone = 1
    onetomany = 2
    manytoone = 3
    manytomany = 4

def get_association_type(end1_multiplicity,end2_multiplicity):
    if end1_multiplicity in ('1', '0..1') and end2_multiplicity in ('1', '0..1'):
        return AssociationType.onetoone
    elif end1_multiplicity in ('1', '0..1') and end2_multiplicity in ('0..*', '1..*'):
        return AssociationType.onetomany
    elif end1_multiplicity in ('0..*', '1..*','none') and end2_multiplicity in ('1', '0..1'):
        return AssociationType.manytoone
    else:
        raise Exception('not support association type (%s--%s)' % (end1_multiplicity,end2_multiplicity) )

    
class UmlAssociation(MoUmlElement):
    end1=dict
    end2 =dict

    @property
    def end1Ref(self):
        return self.end1.reference

    @property
    def end2Ref(self):
        return self.end2.reference


class UMLGeneralization(MoUmlElement):
    source =dict
    target = dict
    _generalize =False
    def extraLoad(self,parser):
        super().extraLoad(parser)
        self.ancestor =parser.getRef(self.target)
        # self.association =parser.getRef(self.associationSide)
    @property
    def is_generalize(self):
        return self._generalize
    def set_generalize(self):
        if not self._generalize:
            self._generalize =True



class UmlSignal(UmlClass):
    pass

class UmlDataType(UmlClass):
    pass

class UmlPrimitiveType(UmlClass):
    pass

class UmlOperation(MoUmlElement):
    parameters =list


class UmlTemplateParameter(UmlAttrBase):
    pass

def uml_loads(filename):
    parser = UmlParser()
    parser.load(filename)
    return parser


