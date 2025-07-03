#!/bin/bash

# Consensus ETL Crawler 다중 노드 배포 스크립트
# Private Cloud 환경의 모든 노드에 배포

echo "=== Consensus ETL Crawler 다중 노드 배포 시작 ==="

# 환경 변수
NODES=("node1" "node2" "node3")
PROJECT_NAME="consensus-etl"
ENV_NAME="etl"  # Private Cloud에 이미 존재하는 환경 사용
PYTHON_VERSION="3.11"
PROJECT_DIR="/app/consensus-etl"
DATA_DIR="/nfs/consensus-data"
DEPLOY_DIR="/home/etluser/consensus-etl-deploy"

# 단일 노드 배포 함수
deploy_to_node() {
    local node=$1
    echo ""
    echo "=== $node 배포 시작 ==="
    
    # SSH로 해당 노드에 연결하여 배포 실행
    ssh $node << EOF
        # 현재 노드 정보 출력
        echo "현재 노드: \$(hostname)"
        echo "사용자: \$(whoami)"
        
        # 기존 conda 환경 확인
        echo "기존 conda 환경 목록:"
        conda env list 2>/dev/null || echo "conda가 설치되지 않았거나 PATH에 없습니다."
        
        # miniconda 설치 확인
        if [ ! -d "/app/miniconda3" ]; then
            echo "⚠️  miniconda3가 설치되지 않음: /app/miniconda3"
            echo "관리자에게 miniconda3 설치를 요청하세요."
            exit 1
        fi
        
        # 환경 변수 설정
        export PATH="/app/miniconda3/bin:\$PATH"
        
        # 필요한 디렉토리 생성
        echo "디렉토리 생성 중..."
        sudo mkdir -p $PROJECT_DIR
        sudo mkdir -p $DATA_DIR/downloads
        sudo mkdir -p $DATA_DIR/logs
        sudo mkdir -p $DATA_DIR/parsed_data
        sudo mkdir -p $DATA_DIR/backups
        
        # 소유권 설정
        sudo chown -R etluser:etluser $PROJECT_DIR
        sudo chown -R etluser:etluser $DATA_DIR
        
        # 프로젝트 파일 복사 (NFS 공유 디렉토리에서)
        if [ -d "$DEPLOY_DIR" ]; then
            echo "프로젝트 파일 복사 중..."
            sudo cp -r $DEPLOY_DIR/* $PROJECT_DIR/
            sudo chown -R etluser:etluser $PROJECT_DIR
        else
            echo "⚠️  배포 파일을 찾을 수 없음: $DEPLOY_DIR"
            exit 1
        fi
        
        # Python 환경 생성
        echo "Python 환경 확인 및 생성 중..."
        if conda env list | grep -q "^$ENV_NAME"; then
            echo "환경 $ENV_NAME 이미 존재합니다."
            echo "기존 환경을 사용합니다."
        else
            echo "새로운 환경 $ENV_NAME 생성 중..."
            sudo conda create -n $ENV_NAME python=$PYTHON_VERSION -y
            
            if [ \$? -eq 0 ]; then
                echo "환경 $ENV_NAME 생성 완료"
            else
                echo "❌ 환경 생성 실패!"
                exit 1
            fi
        fi
        
        # 권한 설정
        sudo setfacl -R -m user::rwx /app/miniconda3
        sudo setfacl -R -m group::rwx /app/miniconda3
        
        # 패키지 설치
        echo "패키지 설치 중..."
        cd $PROJECT_DIR
        PYTHON_FULLPATH="/app/miniconda3/envs/$ENV_NAME/bin/python"
        
        \$PYTHON_FULLPATH -m pip install --upgrade pip
        \$PYTHON_FULLPATH -m pip install -r requirements.txt
        
        # 권한 설정
        chmod +x $PROJECT_DIR/*.sh 2>/dev/null || true
        find $PROJECT_DIR -name "*.py" -exec chmod +x {} \; 2>/dev/null || true
        
        # 설정 파일 조정
        if [ -f "$PROJECT_DIR/crawling/cloud_config.py" ]; then
            cp $PROJECT_DIR/crawling/cloud_config.py $PROJECT_DIR/crawling/config.py
        fi
        
        # 배포 검증
        echo "배포 검증 중..."
        echo "✓ Python 버전: \$(\$PYTHON_FULLPATH --version)"
        echo "✓ 프로젝트 디렉토리: \$([ -d $PROJECT_DIR ] && echo '존재' || echo '없음')"
        echo "✓ 데이터 디렉토리: \$([ -d $DATA_DIR ] && echo '존재' || echo '없음')"
        
        echo "$node 배포 완료!"
EOF
    
    if [ $? -eq 0 ]; then
        echo "✅ $node 배포 성공"
    else
        echo "❌ $node 배포 실패"
        return 1
    fi
}

# 배포 전 준비사항 확인
echo "배포 전 준비사항 확인..."

# 현재 노드가 gate인지 확인
if [ "$(hostname)" != "gate" ]; then
    echo "⚠️  이 스크립트는 gate 노드에서 실행해야 합니다."
    echo "현재 노드: $(hostname)"
    exit 1
fi

# 배포 파일 존재 확인
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "❌ 배포 파일을 찾을 수 없습니다: $DEPLOY_DIR"
    echo "먼저 파일을 업로드하세요."
    exit 1
fi

# 모든 노드에 순차적으로 배포
success_count=0
for node in "${NODES[@]}"; do
    deploy_to_node $node
    if [ $? -eq 0 ]; then
        ((success_count++))
    fi
    
    # 노드 간 잠시 대기
    sleep 2
done

# 배포 결과 요약
echo ""
echo "=== 배포 결과 요약 ==="
echo "총 노드 수: ${#NODES[@]}"
echo "성공한 노드 수: $success_count"
echo "실패한 노드 수: $((${#NODES[@]} - success_count))"

if [ $success_count -eq ${#NODES[@]} ]; then
    echo "🎉 모든 노드에 성공적으로 배포되었습니다!"
    echo ""
    echo "실행 방법:"
    echo "  ssh node1"
    echo "  cd $PROJECT_DIR"
    echo "  ./run_crawler.sh all"
else
    echo "⚠️  일부 노드에서 배포가 실패했습니다."
    echo "실패한 노드를 확인하고 다시 시도하세요."
fi
