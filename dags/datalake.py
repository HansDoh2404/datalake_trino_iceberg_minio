import pandas as pd
from datetime import datetime
from airflow.models.dag import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.standard.operators.python import PythonOperator


def process_csv_to_sql(csv_path="data/youtube_video.csv", **context):
    
    df = pd.read_csv(csv_path)[:100]
    values_list = []
    
    def escape_apostrophes(text):
        """Échappe les apostrophes simples pour SQL."""
        if pd.isna(text):
            return ""
        return str(text).replace("'", "''")
    
    for _, row in df.iterrows():
        col1 = escape_apostrophes(row["video_id"])
        col2 = escape_apostrophes(row["title"])
        col3 = escape_apostrophes(row["channel_name"])
        col4 = escape_apostrophes(row["channel_id"])
        col5 = int(row["view_count"])
        col6 = int(row["like_count"])
        col7 = int(row["comment_count"])
        col8 = datetime.strptime(row["published_date"], "%Y-%m-%dT%H:%M:%SZ")
        col9 = escape_apostrophes(row["thumbnail"])
        
        values_list.append(f"('{col1}', '{col2}', '{col3}', '{col4}', {col5}, {col6}, {col7}, TIMESTAMP '{col8}', '{col9}')")
        
    sql_values = ',\n            '.join(values_list)
    context['ti'].xcom_push(key='sql_values', value=sql_values)
  
    
with DAG(
    dag_id="data_lake_id",
    start_date=datetime(2025, 9, 22),
    schedule=None,  
    catchup=False,
    tags=['trino', 'iceberg', 'minio']
) as dag :

    process_csv = PythonOperator(
        task_id='process_csv',
        python_callable=process_csv_to_sql
    )
    
    insert_into_minio = SQLExecuteQueryOperator(
        task_id='create_iceberg_schema',
        conn_id='trino_conn',
        sql="""INSERT INTO iceberg.test_schema.youtube_video 
               VALUES 
               {{ ti.xcom_pull(task_ids='process_csv', key='sql_values') }}
        """,
        handler=list,
    )
    
    process_csv >> insert_into_minio