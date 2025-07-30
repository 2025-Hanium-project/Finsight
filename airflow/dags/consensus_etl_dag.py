from datetime import datetime, timedelta
from airflow import DAG
import pendulum

seoul = pendulum.timezone("Asia/Seoul")

try:
    from airflow.providers.standard.operators.bash import BashOperator
    from airflow.providers.standard.operators.python import PythonOperator
except ImportError:
    from airflow.operators.bash import BashOperator
    from airflow.operators.python import PythonOperator



# DAG 기본 설정
default_args = {
    'owner': 'etluser',
    'depends_on_past': False,
    'start_date': pendulum.datetime(2025, 7, 9, tz=seoul),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG 정의

dag = DAG(
    'consensus_etl_pipeline',
    default_args=default_args,
    description='Consensus ETL Pipeline for Financial Data',
    schedule='0 3 * * *',  # 매일 새벽 3시에 실행
    catchup=False,
    max_active_runs=1,
    max_active_tasks_per_dag = 24,
    tags=['etl', 'consensus', 'financial']
)

# 크롤러 실행 태스크들
crawlers = [
    'bnk', 'daishin', 'ds', 'hana', 'heungkuk', 'hk',
    'ibks', 'im', 'kiwoom', 'kyobo', 'mirae', 'naver',
    'sangsangin', 'shinhan', 'yj', 'yuanta', 'fnguide',
    'hyundai', 'krx', 'maeil', 'paxnet', 'samsung', 'wisereport',
]

crawler_tasks = []
for crawler in crawlers:
    crawler_tasks.append(
        BashOperator(
            task_id=f'crawl_{crawler}',
            bash_command=f'''
            cd /home/etluser/Finsight-service/Consensus-ETL/project
            /app/miniconda3/envs/etl/bin/python crawling/{crawler}_con_crawler.py
            ''',
            dag=dag,
            retries=3,
            retry_delay=timedelta(minutes=2)
        )
    )


# 태스크 의존성 설정은 필요 없음 (단일 태스크 리스트만 실행)
