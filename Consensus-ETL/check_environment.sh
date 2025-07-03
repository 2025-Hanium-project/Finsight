#!/bin/bash

# Private Cloud ETL 환경 확인 스크립트

echo "=== Private Cloud ETL 환경 확인 ==="
echo "현재 노드: $(hostname)"
echo "현재 사용자: $(whoami)"
echo "실행 시간: $(date)"

# 1. Conda 환경 확인
echo ""
echo "1. Conda 환경 목록:"
if command -v conda &> /dev/null; then
    conda env list
else
    echo "❌ conda 명령어를 찾을 수 없습니다."
fi

# 2. ETL 환경 상세 확인
echo ""
echo "2. ETL 환경 상세 정보:"
ETL_ENV_PATH="/app/miniconda3/envs/etl"

if [ -d "$ETL_ENV_PATH" ]; then
    echo "✅ ETL 환경 경로 존재: $ETL_ENV_PATH"
    echo "   소유자: $(ls -ld $ETL_ENV_PATH | awk '{print $3":"$4}')"
    echo "   권한: $(ls -ld $ETL_ENV_PATH | awk '{print $1}')"
    
    # Python 실행 가능 여부 확인
    PYTHON_PATH="$ETL_ENV_PATH/bin/python"
    if [ -f "$PYTHON_PATH" ]; then
        echo "✅ Python 실행 파일 존재: $PYTHON_PATH"
        echo "   Python 버전: $($PYTHON_PATH --version 2>&1)"
        
        # 주요 패키지 설치 확인
        echo ""
        echo "3. 주요 패키지 설치 상태:"
        packages=(selenium requests beautifulsoup4 pandas mariadb kafka-python pdfplumber)
        
        for package in "${packages[@]}"; do
            if $PYTHON_PATH -c "import $package" 2>/dev/null; then
                version=$($PYTHON_PATH -c "import $package; print(getattr($package, '__version__', 'unknown'))" 2>/dev/null)
                echo "   ✅ $package: $version"
            else
                echo "   ❌ $package: 설치되지 않음"
            fi
        done
        
    else
        echo "❌ Python 실행 파일 없음: $PYTHON_PATH"
    fi
else
    echo "❌ ETL 환경 경로 없음: $ETL_ENV_PATH"
fi

# 3. 프로젝트 디렉토리 확인
echo ""
echo "4. 프로젝트 디렉토리 확인:"
PROJECT_DIR="/app/consensus-etl"
if [ -d "$PROJECT_DIR" ]; then
    echo "✅ 프로젝트 디렉토리 존재: $PROJECT_DIR"
    echo "   파일 목록:"
    ls -la $PROJECT_DIR | head -10
else
    echo "❌ 프로젝트 디렉토리 없음: $PROJECT_DIR"
fi

# 4. 데이터 디렉토리 확인
echo ""
echo "5. 데이터 디렉토리 확인:"
DATA_DIR="/nfs/consensus-data"
if [ -d "$DATA_DIR" ]; then
    echo "✅ 데이터 디렉토리 존재: $DATA_DIR"
    echo "   하위 디렉토리:"
    ls -la $DATA_DIR
else
    echo "❌ 데이터 디렉토리 없음: $DATA_DIR"
fi

# 5. Chrome 설치 확인
echo ""
echo "6. Chrome 설치 확인:"
if command -v google-chrome &> /dev/null; then
    echo "✅ Chrome 설치됨: $(google-chrome --version)"
else
    echo "❌ Chrome 설치되지 않음"
fi

# 6. 실행 권한 확인
echo ""
echo "7. 실행 권한 확인:"
if [ -f "$PROJECT_DIR/run_crawler.sh" ]; then
    if [ -x "$PROJECT_DIR/run_crawler.sh" ]; then
        echo "✅ run_crawler.sh 실행 권한 있음"
    else
        echo "❌ run_crawler.sh 실행 권한 없음"
    fi
else
    echo "❌ run_crawler.sh 파일 없음"
fi

# 요약
echo ""
echo "=== 환경 점검 요약 ==="
if [ -d "$ETL_ENV_PATH" ] && [ -f "$PYTHON_PATH" ] && [ -d "$PROJECT_DIR" ]; then
    echo "🎉 환경 설정 완료! 크롤러 실행 가능합니다."
    echo ""
    echo "실행 방법:"
    echo "   cd $PROJECT_DIR"
    echo "   ./run_crawler.sh [크롤러명|all]"
else
    echo "⚠️  환경 설정이 불완전합니다. 배포를 다시 실행하세요."
    echo ""
    echo "배포 방법:"
    echo "   ./deploy_to_cloud.sh (단일 노드)"
    echo "   ./deploy_multi_node.sh (전체 노드)"
fi
