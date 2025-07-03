#!/bin/bash

# Consensus ETL Crawler 배포 스크립트
# Private Cloud 환경에서 실행

echo "=== Consensus ETL Crawler 배포 시작 ==="

# 1. 환경 변수 설정
export PROJECT_NAME="consensus-etl"
export ENV_NAME="etl"  # Private Cloud에 이미 존재하는 환경 사용
export PYTHON_VERSION="3.11"
export PROJECT_DIR="/app/consensus-etl"
export DATA_DIR="/nfs/consensus-data"
export DEPLOY_DIR="/home/etluser/consensus-etl-deploy"

# 2. 현재 디렉토리 확인
echo "현재 디렉토리: $(pwd)"
echo "배포 파일 목록:"
ls -la

# 3. 필요한 디렉토리 생성
echo "디렉토리 생성 중..."
sudo mkdir -p $PROJECT_DIR
sudo mkdir -p $DATA_DIR
sudo mkdir -p $DATA_DIR/downloads
sudo mkdir -p $DATA_DIR/logs
sudo mkdir -p $DATA_DIR/parsed_data
sudo mkdir -p $DATA_DIR/backups

# 4. 소유권 설정
sudo chown -R etluser:etluser $PROJECT_DIR
sudo chown -R etluser:etluser $DATA_DIR

# 5. 프로젝트 파일 복사
echo "프로젝트 파일 복사 중..."
sudo cp -r $DEPLOY_DIR/* $PROJECT_DIR/
sudo chown -R etluser:etluser $PROJECT_DIR

# 6. Python 환경 생성 (Private Cloud 가이드라인 준수)
echo "Python 환경 확인 및 생성 중..."

# 6-1. 기존 환경 조회
echo "기존 Conda 환경 목록:"
sudo conda env list

# 6-2. 환경이 이미 존재하는지 확인
if sudo conda env list | grep -q "^$ENV_NAME"; then
    echo "환경 $ENV_NAME 이미 존재합니다."
    echo "기존 환경을 사용합니다."
    
    # 기존 환경의 Python 버전 확인
    EXISTING_PYTHON_VERSION=$(sudo /app/miniconda3/envs/$ENV_NAME/bin/python --version 2>&1 | cut -d' ' -f2)
    echo "기존 환경의 Python 버전: $EXISTING_PYTHON_VERSION"
else
    echo "새로운 환경 $ENV_NAME 생성 중..."
    # Private Cloud 가이드라인: root 계정으로 conda create 실행
    sudo conda create -n $ENV_NAME python=$PYTHON_VERSION -y
    
    if [ $? -eq 0 ]; then
        echo "환경 $ENV_NAME 생성 완료"
    else
        echo "환경 생성 실패! 스크립트를 종료합니다."
        exit 1
    fi
fi

# 6-3. Private Cloud 가이드라인: setfacl로 권한 설정
echo "Conda 환경 권한 설정 중..."
sudo setfacl -R -m user::rwx /app/miniconda3
sudo setfacl -R -m group::rwx /app/miniconda3
sudo setfacl -R -m other::r-x /app/miniconda3

# 환경 생성 후 권한 확인
echo "생성된 환경 정보:"
ls -la /app/miniconda3/envs/ | grep $ENV_NAME

# 7. 패키지 설치 (Private Cloud 가이드라인: fullpath 사용)
echo "패키지 설치 중..."
cd $PROJECT_DIR

# Private Cloud 가이드라인: fullpath로 pip 실행
PYTHON_FULLPATH="/app/miniconda3/envs/$ENV_NAME/bin/python"
PIP_FULLPATH="/app/miniconda3/envs/$ENV_NAME/bin/pip"

echo "Python 경로: $PYTHON_FULLPATH"
echo "Python 버전 확인:"
$PYTHON_FULLPATH --version

echo "pip 업그레이드 중..."
$PYTHON_FULLPATH -m pip install --upgrade pip

echo "requirements.txt 패키지 설치 중..."
if [ -f "requirements.txt" ]; then
    $PYTHON_FULLPATH -m pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo "패키지 설치 완료"
    else
        echo "패키지 설치 중 오류 발생!"
        exit 1
    fi
else
    echo "requirements.txt 파일을 찾을 수 없습니다!"
    exit 1
fi

# 설치된 패키지 목록 확인
echo "설치된 패키지 목록:"
$PYTHON_FULLPATH -m pip list

# 8. Chrome 및 ChromeDriver 설치 (Headless 환경용)
echo "Chrome 설치 확인 중..."
if ! command -v google-chrome &> /dev/null; then
    echo "Chrome 설치 중..."
    sudo yum install -y google-chrome-stable || sudo dnf install -y google-chrome-stable
else
    echo "Chrome이 이미 설치되어 있습니다."
fi

# 9. 권한 설정
chmod +x $PROJECT_DIR/*.sh
find $PROJECT_DIR -name "*.py" -exec chmod +x {} \;

# 10. 설정 파일 환경별 조정
echo "설정 파일 조정 중..."
cd $PROJECT_DIR/crawling
# config.py를 cloud_config.py로 대체
if [ -f "cloud_config.py" ]; then
    cp cloud_config.py config.py
    echo "Cloud 환경 설정으로 변경 완료"
fi

echo "=== 배포 완료 ==="
echo "프로젝트 디렉토리: $PROJECT_DIR"
echo "데이터 디렉토리: $DATA_DIR"
echo "Python 환경: $ENV_NAME"
echo "Python 경로: $PYTHON_FULLPATH"

# 11. 배포 검증
echo ""
echo "=== 배포 검증 ==="

# 11-1. 디렉토리 구조 확인
echo "1. 디렉토리 구조 확인:"
echo "   프로젝트 디렉토리 존재: $([ -d $PROJECT_DIR ] && echo '✓' || echo '✗')"
echo "   데이터 디렉토리 존재: $([ -d $DATA_DIR ] && echo '✓' || echo '✗')"
echo "   크롤링 디렉토리 존재: $([ -d $PROJECT_DIR/crawling ] && echo '✓' || echo '✗')"

# 11-2. Python 환경 확인
echo "2. Python 환경 확인:"
echo "   Python 실행 가능: $($PYTHON_FULLPATH --version 2>&1 && echo '✓' || echo '✗')"
echo "   필수 패키지 확인:"
echo "     - selenium: $($PYTHON_FULLPATH -c 'import selenium; print("✓")' 2>/dev/null || echo '✗')"
echo "     - requests: $($PYTHON_FULLPATH -c 'import requests; print("✓")' 2>/dev/null || echo '✗')"
echo "     - pandas: $($PYTHON_FULLPATH -c 'import pandas; print("✓")' 2>/dev/null || echo '✗')"
echo "     - mariadb: $($PYTHON_FULLPATH -c 'import mariadb; print("✓")' 2>/dev/null || echo '✗')"

# 11-3. 실행 권한 확인
echo "3. 실행 권한 확인:"
echo "   run_crawler.sh 실행 가능: $([ -x $PROJECT_DIR/run_crawler.sh ] && echo '✓' || echo '✗')"

# 11-4. Chrome 설치 확인
echo "4. Chrome 설치 확인:"
echo "   Chrome 실행 가능: $(command -v google-chrome >/dev/null 2>&1 && echo '✓' || echo '✗')"

echo ""
echo "실행 명령어: cd $PROJECT_DIR && ./run_crawler.sh [크롤러명|all]"
echo "예시: cd $PROJECT_DIR && ./run_crawler.sh bnk"
