from django.db.models.base import ModelBase  
from django.db import models  
from django.conf import settings

# This exports model base with overridden Meta class that allows to specify schema and table for MSSQL support 
# Ugly string injection hack so that we can access the table under the schema
# See: http://nightlyclosures.com/2019/10/16/working-with-unmanaged-sql-server-in-django-pt-ii/
SQL_DB_FORMAT = '{schema}].[{table}'


class MSSQLDatabaseMeta(ModelBase):

    def __new__(typ, name, bases, attrs, **kwargs):
        super_new = super().__new__

        # Also ensure initialization is only performed for subclasses of Model
        # (excluding Model class itself).
        parents = [b for b in bases if isinstance(b, MSSQLDatabaseMeta)]
        if not parents:
            return super_new(typ, name, bases, attrs)

        meta = attrs.get('Meta', None)
        if not meta:
            meta = super_new(typ, name, bases, attrs, **kwargs).Meta

        # ignore abstract models
        is_abstract = getattr(meta, 'abstract', False)
        if is_abstract:
            return super_new(typ, name, bases, attrs, **kwargs)

        # Ensure table is unmanaged unless explicitly set
        is_managed = getattr(meta, 'managed', False)
        meta.managed = is_managed

        # SQL injection garbage
        meta.db_table = typ.format_db_table(bases, meta)

        # Delete custom attributes so the Meta validation will let the server run
        del meta.mssql_schema
        del meta.mssql_table

        attrs['Meta'] = meta
        return super().__new__(typ, name, bases, attrs, **kwargs)

    @classmethod
    def format_db_table(cls, bases, meta):
      
        table_format = SQL_DB_FORMAT

        return table_format.format(
            schema=meta.mssql_schema,
            table=meta.mssql_table
        )


class MSSQLDatabaseModel(models.Model, metaclass=MSSQLDatabaseMeta):

    #database = 'default'

    class Meta:
        abstract = True