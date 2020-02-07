class Singleton(type):
    def __new__(cls, name,bases,attrs):
        attrs["_instance"] = None
        return super(Singleton,cls).__new__(cls,name,bases,attrs)


    def __call__(self, *args, **kwargs):
        if self._instance is None:
            self._instance = super(Singleton,self).__call__(*args, **kwargs)
        return self._instance