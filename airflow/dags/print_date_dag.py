from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.python import PythonOperator
import httpx
from datetime import datetime
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
}

dag = DAG(
    'example_dag',
    default_args=default_args,
    schedule='@daily',
)


# 기존 BashOperator도 병렬 또는 순차로 연결 가능
task1 = BashOperator(
    task_id='print_date',
    bash_command='date',
    dag=dag,
)

task2 = BashOperator(
    task_id='echo_hello',
    bash_command='echo "Hello, Airflow!"',
    dag=dag,
)

# 원하는 순서대로 연결
task1 >> task2
