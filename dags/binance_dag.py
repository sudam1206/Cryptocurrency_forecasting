from datetime import timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'run_my_app',
    default_args=default_args,
    description='A simple DAG to run my app',
    schedule_interval=timedelta(days=1),
    start_date=days_ago(1),
    tags=['example'],
)

def run_my_task():
    # This function would contain the logic to run  app's task
    print("Running my app task")

run_task = PythonOperator(
    task_id='run_my_app_task',
    python_callable=run_my_task,
    dag=dag,
)

run_task
