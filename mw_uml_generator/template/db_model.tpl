from .model_base import *
{% for tb in dbmodels %}
{% if tb.as_association==False %}
class {{ tb.name|capitalize }}({{ tb.name|capitalize }}Base):
    pass
{% endif %}
{% endfor %}