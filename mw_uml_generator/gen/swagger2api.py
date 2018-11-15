import yaml
import json
import os,sys
from ..template import genTemplate
class ApiRoute:
    def __init__(self,path,method,opid):
        self.path =path
        self.method = method
        self.func = opid
        self.query =[]
        self.headers ={}

    @property
    def has_body(self):
        return self.method in ['post','put']

    @property
    def path_as_url(self):
        return self.path.replace('{','${')
    @property
    def query_as_args(self):
        def add_quote(s):
            return '"%s"' % s
        if len(self.query)>0:
            re =[]
            for param in self.query:
                s =param['name']
                if param.get('default_const'):
                    s+='=%s' % param['default_const']
                elif param.get('default'):
                    s += '=%s' % (add_quote(param['default'] or '') if param['type']=='string' else str(param['default']) )
                re.append(s)
            return '{%s}' % ','.join(re)

    @property
    def header_params(self):
        return [param for param in self.query if param['in']=='header']

    @property
    def query_as_url(self):
        params =[param for param in self.query if param['in']=='query']
        if len(params) > 0:
            re =[]
            for param in params:
                s ='        %s:%s' % (param['name'],param['name'])
                re.append(s)
            return '{\r\n%s}' % ',\r\n'.join(re)

        # if len(params)>0:
        #     re =['%s=${%s}' % (param['name'],param['name']) for param in params ]
        #     return '&'.join(re)



    @property
    def header_as_str(self):
        params = [param for param in self.query if param['in'] == 'header']
        if len(params)>0 or len(self.headers.keys())>0:
            assert json.dumps(self.headers)!='{}' ,params
            return json.dumps(self.headers)



def swagger2api(swagger,outputfile):
    # if not os.path.exists(swagger_file):
    #     sys.exit('swagger 文件不存在。%s' % swagger_file )
    # with open(swagger_file) as f:
    #     swagger = yaml.load(f.read())
    paths=swagger['paths']
    routes =[]
    for path,methods in paths.items():
        for method,method_v in methods.items():
            opid = method_v['operationId'].split('.')[-1]
            apiroute = ApiRoute(path,method.lower(),opid)
            if 'parameters' in method_v.keys():
                params = [param for param in method_v['parameters'] if param['in'] in ('header','query','path')]
                for param in params:
                    if param['name'] == 'page':
                        param['default'] = 1
                    elif param['name'] == 'per_page':
                        param['default_const'] = 'PER_PAGE'


                    apiroute.query.append(param)

                hasForm = len(list(filter(lambda param:param['in']=='formData',method_v['parameters'])))>0
                if hasForm:
                    apiroute.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
                hasFile = len(list(filter(lambda param: param['in'] == 'file',method_v['parameters']))) > 0
                if hasFile:
                    apiroute.headers.update({'Content-Type': 'multipart/form-data'})

            routes.append(apiroute)

    s =genTemplate('swagger2api',basePath = swagger['basePath'],routes = routes)
    with open(outputfile,mode='w') as f:
        f.write(s)


    return s
    # return routes

