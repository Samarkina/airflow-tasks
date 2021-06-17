import uuid
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.hooks.postgres_hook import PostgresHook
from airflow.operators.python import PythonOperator
from airflow.operators.python_operator import BranchPythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from custom_operator.postgresql_count_rows_operator import PostgreSQLCountRowsOperator

DATABASE = "123"

config = {
    'dag_id_1': {
        'schedule_interval': "*/15 * * * *",
        'default_args': {
            'owner': 'admin',
            'start_date': datetime(2021, 4, 18)
        },
        'table_name': 'table_name_1'
    },
    'dag_id_2': {
        'schedule_interval': "*/15 * * * *",
        'default_args': {
            'owner': 'admin',
            'start_date': datetime(2021, 4, 18)
        },
        'table_name': 'table_name_2'
    },
    'dag_id_3': {
        'schedule_interval': "*/15 * * * *",
        'default_args': {
            'owner': 'admin',
            'start_date': datetime(2021, 4, 18)
        },
        'table_name': 'table_name_3'
    }
}


def read_sql(path):
    """Read file from the passing path

    :param path: path to sql file
    :return: data from file
    """
    with open(path, "r") as f:
        return f.read()


for dag_id in config:
    with DAG(dag_id,
             default_args=config[dag_id]['default_args'],
             schedule_interval=config[dag_id]['schedule_interval']) as dag:

        def print_func(**kwargs):
            """ print information to the logs"""
            return "{0} start processing tables in database: {1}".format(kwargs['dag_id'], kwargs['database'])

        task_print = PythonOperator(
            task_id='print_the_context',
            python_callable=print_func,
            op_kwargs={
                "dag_id": dag.dag_id,
                "database": DATABASE
            }
        )

        task_get_current_user = BashOperator(
            task_id='get_current_user',
            bash_command='whoami',
            do_xcom_push=True
        )

        def check_table_exist(sql_to_check_table_exist, table_name):
            """ method to check that table exists """
            hook = PostgresHook()
            # check table exist
            query = hook.get_first(sql=sql_to_check_table_exist.format(table_name))
            if query:
                return 'insert_new_row'
            return 'create_table'

        task_table_exist = BranchPythonOperator(
            task_id='check_table_exist',
            python_callable=check_table_exist,
            op_kwargs={
                "sql_to_check_table_exist": read_sql("./scripts/SQLs/sql_to_check_table_exist.sql"),
                "table_name": config[dag.dag_id]['table_name']
            },
            provide_context=True
        )

        task_create = PostgresOperator(
            task_id='create_table',
            postgres_conn_id="postgres_default",
            sql=read_sql("./scripts/SQLs/create_table.sql"),
            params={
                'table_name': config[dag.dag_id]['table_name']
            }
        )

        task_insert = PostgresOperator(
            task_id='insert_new_row',
            trigger_rule='none_failed',
            postgres_conn_id="postgres_default",
            sql=read_sql("./scripts/SQLs/insert_data.sql"),
            params={
                'table_name': config[dag.dag_id]['table_name']
            },
            parameters={
                'custom_id_value': uuid.uuid4().int % 123456789,
                'user_name_value': "{{ ti.xcom_pull(task_ids='get_current_user') }}",
                'timestamp_value': datetime.now(),

            }
        )

        task_query = PostgreSQLCountRowsOperator(
            task_id='query_the_table',
            table_name=config[dag.dag_id]['table_name']
        )

        task_print >> task_get_current_user >> task_table_exist >> task_create >> \
            task_insert >> task_query

        task_table_exist >> task_insert

        globals()[dag.dag_id] = dag
