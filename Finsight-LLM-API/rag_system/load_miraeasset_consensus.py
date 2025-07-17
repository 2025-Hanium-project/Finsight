import pandas as pd
from data_loader import insert_csv_to_db

# 미래에셋 리포트 CSV 경로
csv_path = '../../Consensus-ETL/project/consensus_parsed/miraeasset_consensus_reports.csv'

def main():
    df = pd.read_csv(csv_path)
    # title: 종목명 + ' ' + 컨센서스 제목
    df['title'] = df['종목명'].fillna('') + ' ' + df['컨센서스 제목'].fillna('')
    # text: title을 제외한 모든 컬럼을 문자열로 합침
    text_cols = [col for col in df.columns if col not in ['종목명', '컨센서스 제목']]
    df['text'] = df[text_cols].astype(str).apply(lambda row: ' '.join(row.values), axis=1)
    # 필요한 컬럼만 추출
    df = df[['title', 'text']]
    # 임시 파일로 저장 후 적재
    temp_path = 'miraeasset_consensus_temp.csv'
    df.to_csv(temp_path, index=False)
    insert_csv_to_db(temp_path, 'consensus_reports', title_col='title', text_col='text')
    print('미래에셋 consensus 리포트 적재 완료')

if __name__ == '__main__':
    main()
