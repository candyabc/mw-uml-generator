import sqlalchemy as db
from sqlalchemy import Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

{% include "./db_model_define.tpl" %}

if __name__ == "__main__":
    pass
    # engine = db.create_engine("")
