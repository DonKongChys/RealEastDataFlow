from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipelines.restate_pipeline import run_scraping_task

# Define the DAG
default_args = {
    'owner': 'tridoan',
    'depends_on_past': False,
    'start_date': datetime(2024, 8, 8),
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
    'email_on_failure': False,
    'email_on_retry': False
}

dag = DAG(
    'restate_data_flow',
    default_args=default_args,
    description='DAG to scrape, transform, and load real estate data',
    schedule_interval=None,
    catchup=False
)

# Define the tasks
run_task = PythonOperator(
    task_id="run_scraping_task",
    python_callable=run_scraping_task,
    provide_context=True,
    dag=dag
)

# Define the task dependencies
run_task