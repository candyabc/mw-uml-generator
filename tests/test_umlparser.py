from __future__ import print_function, absolute_import, division


import pytest
import sys
import os

# metaclass是创建类，所以必须从`type`类型派生：
gg ={}
class Singleton(type):
    def __new__(cls, name,bases,attrs):
        print("__new__")
        print(bases)
        attrs["_instance"] = None
        new_cls = super(Singleton,cls).__new__(cls,name,bases,attrs)
        gg[name] = new_cls
        # print['name',new_cls]
        return  new_cls

    # def __call__(self, *args, **kwargs):
    #     print ("__call__")
    #     if self._instance is None:
    #         self._instance = super(Singleton,self).__call__(*args, **kwargs)
    #     return self._instance
class FA():
    def __init__(self):
        self.a ='heool'
class Foo(FA, metaclass=Singleton):
    pass

class TestClass:
    def test_mya(self):
        # foo1 = Foo()
        # foo2 = Foo()
        # print(Foo.__dict__ )
        # print(['a',foo1.a] )
        print(['gg',gg])
        f1 =gg['Foo']()
        print(f1.__dict__)
        # assert len(gg.keys())>0
    # def test_factory(self):
    #     print(_umlParseFactory._classMapping)
    #     assert len(_umlParseFactory._classMapping.keys())>0