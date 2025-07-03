from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# DAG 기본 설정
default_args = {
    'owner': 'etluser',
    'depends_on_past': False,
    'start_date': days_ago(1),
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
    schedule_interval='0 9 * * 1-5',  # 평일 오전 9시
    catchup=False,
    max_active_runs=1,
    tags=['etl', 'consensus', 'financial']
)

# 크롤러 실행 태스크들
crawlers = [
    'bnk', 'daishin', 'ds', 'hana', 'heungkuk', 'hk', 
    'ibks', 'im', 'kiwoom', 'kyobo', 'mirae', 'naver', 
    'sangsangin', 'shinhan', 'yj', 'yuanta'
]

# 환경 준비 태스크
prepare_env = BashOperator(
    task_id='prepare_environment',
    bash_command='''
    cd /app/consensus-etl
    mkdir -p /nfs/consensus-data/downloads/$(date +%Y%m%d)
    mkdir -p /nfs/consensus-data/logs/$(date +%Y%m%d)
    echo "Environment prepared for $(date)"
    ''',
    dag=dag
)

# 크롤러 태스크 생성
crawler_tasks = []
for crawler in crawlers:
    task = BashOperator(
        task_id=f'crawl_{crawler}',
        bash_command=f'''
        cd /app/consensus-etl
        /app/miniconda3/envs/etl-crawler/bin/python crawling/{crawler}_con_crawler.py
        ''',
        dag=dag,
        pool='crawler_pool',  # 동시 실행 제한
        retries=2,
        retry_delay=timedelta(minutes=10)
    )
    crawler_tasks.append(task)

# 데이터 검증 태스크
def validate_data(**context):
    """크롤링된 데이터 검증"""
    import os
    from datetime import datetime
    
    today = datetime.now().strftime('%Y%m%d')
    download_path = f"/nfs/consensus-data/downloads/{today}"
    
    if not os.path.exists(download_path):
        raise ValueError(f"Download directory not found: {download_path}")
    
    files = os.listdir(download_path)
    file_count = len(files)
    
    print(f"Total files downloaded: {file_count}")
    
    if file_count == 0:
        raise ValueError("No files were downloaded")
    
    return file_count

validate_task = PythonOperator(
    task_id='validate_data',
    python_callable=validate_data,
    dag=dag
)

# 데이터 정리 태스크
cleanup_task = BashOperator(
    task_id='cleanup_old_data',
    bash_command='''
    # 7일 이상 된 다운로드 파일 삭제
    find /nfs/consensus-data/downloads -type d -mtime +7 -exec rm -rf {} +
    
    # 30일 이상 된 로그 파일 삭제
    find /nfs/consensus-data/logs -type f -mtime +30 -delete
    
    echo "Cleanup completed"
    ''',
    dag=dag
)

# 태스크 의존성 설정
prepare_env >> crawler_tasks
crawler_tasks >> validate_task >> cleanup_task
