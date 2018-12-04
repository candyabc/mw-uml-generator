import sqlalchemy as db
from sqlalchemy import MetaData,Table
from sqlalchemy.orm import relationship

metadata =MetaData()

{% for tb in dbmodels %}
{{ tb.name.lower()}}s = Table('{{ tb.name.lower() }}', metadata,
    {% for line in tb.render_as_columns() %}
    {{ line }}{% if not loop.last %},
    {% endif %}
    {% endfor %}
)

{% endfor %}

