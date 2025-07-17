import pandas as pd
from db import get_conn
from embedding import get_embedding

def insert_csv_to_db(csv_path, table_name, title_col='title', text_col='text'):
    df = pd.read_csv(csv_path)
    with get_conn() as conn:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                text = row[text_col] if text_col in row else row.get('내용', '')
                title = row[title_col] if title_col in row else row.get('제목', '')
                emb = get_embedding(text)
                emb_str = '[' + ','.join(str(x) for x in emb) + ']'
                cur.execute(
                    f"INSERT INTO {table_name} (title, text, embedding) VALUES (%s, %s, %s)",
                    (title, text, emb_str)
                )
        conn.commit()
