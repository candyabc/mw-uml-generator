import sqlalchemy as db
from sqlalchemy import Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum

Base = declarative_base()

{% for enum_profile in enum_profiles %}
class {{ enum_profile.name|capitalize }}(Enum):
    {% if enum_profile.title|length > 0 %}
    '''
    {{ enum_profile.title }}
    '''
    {% endif %}
    {% for literal in enum_profile.literals %}
    {{ literal[0]|lower }} = {{ loop.index0 }} # {{ literal[1] }}
    {% endfor %}
{% endfor %}

{% include "./db_model_define.tpl" %}

if __name__ == "__main__":
    pass
    # engine = db.create_engine("")
