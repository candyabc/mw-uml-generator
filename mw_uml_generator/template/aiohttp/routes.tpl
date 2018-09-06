
BASEPATH='{{ basepath }}'

{% for tag in tags %}
from .{{ tag }} import *
{% endfor %}

def gen_full_url(endpoint):
    return BASEPATH+endpoint

def config_routes(app):
{% for operation in operations %}
    app.router.add_{{ operation.method }}(gen_full_url('{{ operation.pathname }}'),{{ operation.operatorid }})
{% endfor %}
    pass