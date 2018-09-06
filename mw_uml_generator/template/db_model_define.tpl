{% for tb in dbmodels %}
{% if tb.as_association %}
{{ tb.name.lower()}} = Table('{{ tb.name.lower() }}', {{ modelclass }}.metadata,
    {% for fd in tb.fields %}
        {{ fd.render_foreign_id() }}
    {% endfor %}
)
{% else %}
class {{ tb.name|capitalize }}Base({{ modelclass }}):
    __tablename__ = '{{ tb.name.lower()  }}'
    {% for field in tb.fields %}
        {% for line in field.render() %}
    {{ line }}
        {% endfor %}
    {% endfor %}
{% endif %}

{% endfor %}
