#!/bin/bash

# Consensus ETL Crawler 실행 스크립트
# Private Cloud 환경에서 사용

# 환경 변수
ENV_NAME="etl"  # Private Cloud에 이미 존재하는 환경 사용
PROJECT_DIR="/app/consensus-etl"
DATA_DIR="/nfs/consensus-data"

# Private Cloud 가이드라인: fullpath로 Python 경로 설정
PYTHON_PATH="/app/miniconda3/envs/$ENV_NAME/bin/python"

# 작업 디렉토리로 이동
cd $PROJECT_DIR

echo "=== Consensus ETL Crawler 실행 ==="
echo "실행 시간: $(date)"
echo "현재 노드: $(hostname)"
echo "Python 경로: $PYTHON_PATH"
echo "데이터 디렉토리: $DATA_DIR"

# Python 환경 확인
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Python 환경을 찾을 수 없습니다: $PYTHON_PATH"
    echo "배포를 먼저 실행하세요: ./deploy_to_cloud.sh 또는 ./deploy_multi_node.sh"
    exit 1
fi

echo "Python 버전: $($PYTHON_PATH --version)"

# 로그 파일 설정
LOG_FILE="$DATA_DIR/logs/crawler_$(date +%Y%m%d_%H%M%S).log"

# 크롤러 실행 함수
run_crawler() {
    local crawler_name=$1
    echo "[$crawler_name 크롤러 시작] $(date)" | tee -a $LOG_FILE
    
    $PYTHON_PATH crawling/${crawler_name}_con_crawler.py 2>&1 | tee -a $LOG_FILE
    
    if [ $? -eq 0 ]; then
        echo "[$crawler_name 크롤러 완료] $(date)" | tee -a $LOG_FILE
    else
        echo "[$crawler_name 크롤러 오류] $(date)" | tee -a $LOG_FILE
    fi
}

# 사용법 출력
if [ $# -eq 0 ]; then
    echo "사용법: $0 [크롤러명|all]"
    echo ""
    echo "사용 가능한 크롤러:"
    echo "  bnk, daishin, ds, hana, heungkuk, hk, ibks, im, kiwoom, kyobo, mirae, naver, sangsangin, shinhan, yj, yuanta"
    echo ""
    echo "예시:"
    echo "  $0 bnk           # BNK 크롤러만 실행"
    echo "  $0 all           # 모든 크롤러 실행"
    exit 1
fi

# 크롤러 실행
if [ "$1" = "all" ]; then
    echo "모든 크롤러를 순차적으로 실행합니다..."
    
    crawlers=(bnk daishin ds hana heungkuk hk ibks im kiwoom kyobo mirae naver sangsangin shinhan yj yuanta)
    
    for crawler in "${crawlers[@]}"; do
        run_crawler $crawler
        sleep 5  # 크롤러 간 5초 대기
    done
    
else
    # 개별 크롤러 실행
    run_crawler $1
fi

echo "=== 실행 완료 ==="
echo "로그 파일: $LOG_FILE"
