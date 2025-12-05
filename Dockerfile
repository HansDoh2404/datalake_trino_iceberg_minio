FROM apache/airflow:3.1.0

RUN pip install --no-cache-dir apache-airflow-providers-trino==6.3.5 pandas
