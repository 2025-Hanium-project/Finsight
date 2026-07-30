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
    max_active_runs=2,
    tags=['etl', 'consensus', 'financial']
)

# 크롤러 실행 태스크들
crawlers = [
    'bnk', 'daishin', 'ds', 'hana', 'heungkuk', 'hk',
    'ibks', 'im', 'kiwoom', 'kyobo', 'mirae', 'naver',
    'sangsangin', 'shinhan', 'yuanta', 'fnguide',
    'hyundai', 'maeil', 'samsung', 'wisereport'
    # 'yj': 로그인 리다이렉트로 비로그인 수집 불가, hk가 유진 리포트 수집
    # 'krx': 현재 수집 대상에서 제외
    # 'paxnet': paxnet 서버에서 실패
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
            retry_delay=timedelta(minutes=2),
            execution_timeout=timedelta(minutes=10)
        )
    )


# 크롤링이 모두 끝나면 수집된 리포트를 LLM API로 파싱해 DB에 저장한다.
# 일부 증권사 크롤러가 실패해도 나머지가 받아온 리포트는 그날 처리해야 하므로
# all_done을 쓴다. 실패한 크롤 태스크는 그대로 failed로 남는다.
save_to_db = BashOperator(
    task_id='save_to_db',
    bash_command='''
    cd /home/etluser/Finsight-service/Consensus-ETL/project
    curl -fsS http://localhost:38000/ > /dev/null
    /app/miniconda3/envs/etl/bin/python save_to_db/save_con_info.py
    ''',
    dag=dag,
    trigger_rule='all_done',
    retries=1,
    retry_delay=timedelta(minutes=5),
    execution_timeout=timedelta(hours=3)
)

crawler_tasks >> save_to_db
