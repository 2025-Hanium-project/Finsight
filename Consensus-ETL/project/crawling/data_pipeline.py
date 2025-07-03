import mariadb
import json
from kafka import KafkaProducer
import logging
from datetime import datetime
from cloud_config import DB_CONFIG, KAFKA_CONFIG

class DataPipeline:
    """Private Cloud 환경에서 크롤링 데이터를 저장하고 전송하는 클래스"""
    
    def __init__(self):
        self.db_connection = None
        self.kafka_producer = None
        self.setup_logging()
        
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/nfs/consensus-data/logs/data_pipeline.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def connect_database(self):
        """MariaDB 연결"""
        try:
            self.db_connection = mariadb.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database']
            )
            self.logger.info("MariaDB 연결 성공")
            return True
        except mariadb.Error as e:
            self.logger.error(f"MariaDB 연결 실패: {e}")
            return False
    
    def create_tables(self):
        """필요한 테이블 생성"""
        if not self.db_connection:
            if not self.connect_database():
                return False
        
        cursor = self.db_connection.cursor()
        
        # 컨센서스 데이터 테이블
        create_table_query = """
        CREATE TABLE IF NOT EXISTS consensus_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            source VARCHAR(50) NOT NULL,
            company_name VARCHAR(100),
            company_code VARCHAR(10),
            report_date DATE,
            target_price DECIMAL(10,2),
            recommendation VARCHAR(20),
            analyst VARCHAR(100),
            file_path VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_source (source),
            INDEX idx_company_code (company_code),
            INDEX idx_report_date (report_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        
        try:
            cursor.execute(create_table_query)
            self.db_connection.commit()
            self.logger.info("테이블 생성 완료")
            return True
        except mariadb.Error as e:
            self.logger.error(f"테이블 생성 실패: {e}")
            return False
        finally:
            cursor.close()
    
    def insert_consensus_data(self, data):
        """컨센서스 데이터 삽입"""
        if not self.db_connection:
            if not self.connect_database():
                return False
        
        cursor = self.db_connection.cursor()
        
        insert_query = """
        INSERT INTO consensus_data 
        (source, company_name, company_code, report_date, target_price, recommendation, analyst, file_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            cursor.execute(insert_query, (
                data.get('source'),
                data.get('company_name'),
                data.get('company_code'),
                data.get('report_date'),
                data.get('target_price'),
                data.get('recommendation'),
                data.get('analyst'),
                data.get('file_path')
            ))
            self.db_connection.commit()
            self.logger.info(f"데이터 삽입 완료: {data.get('company_name')}")
            return True
        except mariadb.Error as e:
            self.logger.error(f"데이터 삽입 실패: {e}")
            return False
        finally:
            cursor.close()
    
    def setup_kafka_producer(self):
        """Kafka Producer 설정"""
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=KAFKA_CONFIG['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            self.logger.info("Kafka Producer 설정 완료")
            return True
        except Exception as e:
            self.logger.error(f"Kafka Producer 설정 실패: {e}")
            return False
    
    def send_to_kafka(self, data):
        """Kafka로 데이터 전송"""
        if not self.kafka_producer:
            if not self.setup_kafka_producer():
                return False
        
        try:
            # 메시지 키는 회사 코드로 설정 (파티셔닝 용)
            key = data.get('company_code', 'unknown')
            
            # 타임스탬프 추가
            data['timestamp'] = datetime.now().isoformat()
            
            self.kafka_producer.send(
                KAFKA_CONFIG['topic'],
                key=key,
                value=data
            )
            self.kafka_producer.flush()
            self.logger.info(f"Kafka 전송 완료: {data.get('company_name')}")
            return True
        except Exception as e:
            self.logger.error(f"Kafka 전송 실패: {e}")
            return False
    
    def process_crawled_data(self, data_list, source):
        """크롤링된 데이터를 처리 (DB 저장 + Kafka 전송)"""
        success_count = 0
        
        for data in data_list:
            data['source'] = source
            
            # DB에 저장
            if self.insert_consensus_data(data):
                # Kafka로 전송
                if self.send_to_kafka(data):
                    success_count += 1
        
        self.logger.info(f"{source}: {success_count}/{len(data_list)} 건 처리 완료")
        return success_count
    
    def close_connections(self):
        """연결 종료"""
        if self.db_connection:
            self.db_connection.close()
            self.logger.info("MariaDB 연결 종료")
        
        if self.kafka_producer:
            self.kafka_producer.close()
            self.logger.info("Kafka Producer 종료")
