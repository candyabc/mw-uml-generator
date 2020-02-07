import connexion
import six
{% for op in operations %}
def {{ op.operatorid }}(**args):
    pass
{% endfor %}