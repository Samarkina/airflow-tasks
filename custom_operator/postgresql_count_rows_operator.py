from airflow.models.baseoperator import BaseOperator

from airflow.hooks.postgres_hook import PostgresHook
from airflow.utils.decorators import apply_defaults


class PostgreSQLCountRowsOperator(BaseOperator):
    """ custom operator that execute query for passing table"""

    @apply_defaults
    def __init__(self, table_name, *args, **kwargs):
        self.table_name = table_name
        self.hook = PostgresHook()
        super(PostgreSQLCountRowsOperator, self).__init__(*args, **kwargs)

    def execute(self, context):
        sql_query = f'SELECT COUNT(*) FROM {self.table_name};'
        result = self.hook.get_first(sql=sql_query)
        context['ti'].xcom_push(key='sql_query', value=result)
        context['ti'].xcom_push(key='run_id', value=context['run_id'])
