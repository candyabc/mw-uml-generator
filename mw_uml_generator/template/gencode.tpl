# uml文件，支持产生swagger,datamodel
uml: {{ uml_file }}
# flask | aiohttp
project: {{ project }}

#用于产生dockercompose file时产生环境变量内容
env:
#  DATABASE_NAME: maxwin

#产生model的设定
model:
  # autoid: true
  # id_name: id
  # id_type: integer
  # id_connector: '_'
  as_model: true

#产生swagger的设定
swagger:
  # hasxml: false
  # auths: []
  # lang: default
  # paginate: true

markdown:


apijs:
  outPath:
  default:
    in:
    out:




