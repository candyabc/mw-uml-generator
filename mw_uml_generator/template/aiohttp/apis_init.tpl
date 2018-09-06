{% for swagger in swaggers %}
from .{{ swagger.name }}_{{ swagger.ver }} import routes as {{ swagger.model_routename() }}
{% endfor %}