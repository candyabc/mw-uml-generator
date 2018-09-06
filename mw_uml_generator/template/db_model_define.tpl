{% for tb in dbmodels %}

{% if tb.as_association %}
{{ tb.name.lower()}} = Table('{{ tb.name.lower() }}', {{ modelclass }}.metadata,
    {% for line in tb.render_fields() %}
    {{ line }}{% if not loop.last %},
    {% endif %}
    {% endfor %}
)
{% else %}
class {{ tb.name|capitalize }}Base({{ modelclass }}):
    {% if tb.title|length > 0 %}
    '''
    {{ tb.title }}
    '''
    {% endif %}
    __tablename__ = '{{ tb.name.lower()  }}'
    {% for line in tb.render_fields() %}
    {{ line }}
    {% endfor %}
{% endif %}

{% endfor %}
