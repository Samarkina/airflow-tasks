import os
from airflow.utils.dates import days_ago

from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.subdag import SubDagOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.sensors.filesystem import FileSensor
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

DAG_NAME = "trigger_dag"
default_args = {
    'owner': 'admin',
    'start_date': days_ago(1)
}
schedule_interval = "@daily"

direct = os.path.dirname(__file__)

path = Variable.get(
    'name_path_variable',
    default_var=os.path.join(direct, "../files/123.txt")
)

with DAG(DAG_NAME,
         default_args=default_args,
         schedule_interval=schedule_interval) as dag:
    task_file_sensor = FileSensor(
        task_id='file_sensor',
        poke_interval=30,
        filepath=path
    )

    task_trigger = TriggerDagRunOperator(
        task_id='trigger_dag',
        trigger_dag_id="dag_id_2"
    )


    def load_sub_dag(parent_dag_name, child_dag_name, args):
        with DAG(
                dag_id='{0}.{1}'.format(parent_dag_name, child_dag_name),
                default_args=args,
                schedule_interval=schedule_interval
        ) as sub_dag:
            task_sensor_success_dag = ExternalTaskSensor(
                task_id='sensor_success_dag',
                external_dag_id=DAG_NAME,
                external_task_id='trigger_dag'
            )

            def print_result_func(**kwargs):
                """ print information to the logs from xcom var"""
                xcom_message = kwargs['ti'].xcom_pull(key="message",
                                                      dag_id="dag_id_1",
                                                      task_ids="xcom_push",
                                                      include_prior_dates=True)
                return xcom_message

            task_print_result = PythonOperator(
                task_id='print_result_from_xcom',
                python_callable=print_result_func
            )

            task_remove_file = BashOperator(
                task_id='remove_file',
                bash_command='rm {}'.format(path)
            )

            execution_date = '{{ ts_nodash }}'
            new_file = os.path.join(direct, "../files/finished_{}").format(execution_date)

            task_create_file = BashOperator(
                task_id='create_file',
                bash_command='touch {}'.format(new_file)
            )

            task_sensor_success_dag >> task_print_result >> task_remove_file >> task_create_file

            return sub_dag


    task_sub_dag = SubDagOperator(
        task_id='sub_dag',
        subdag=load_sub_dag(
            DAG_NAME,
            'sub_dag',
            default_args
        ),
        default_args=default_args
    )


    def slack_alert():
        from slack import WebClient
        from slack.errors import SlackApiError

        from airflow.hooks.base_hook import BaseHook
        conn = BaseHook.get_connection('slack_conn')
        conn_dict: dict = eval(conn.get_extra())
        slack_token = conn_dict['token']
        client = WebClient(token=slack_token)
        try:
            response = client.chat_postMessage(
                channel="slack_channel_name",
                text="Hello from your app! :tada:")
        except SlackApiError as e:
            # You will get a SlackApiError if "ok" is False
            assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'

    slack_alert_task = PythonOperator(
        task_id="alert_to_slack",
        python_callable=slack_alert
    )

    task_file_sensor >> task_trigger >> task_sub_dag >> slack_alert_task
