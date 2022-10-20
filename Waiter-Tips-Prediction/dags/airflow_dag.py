"""
    This module is the main, dag file that contains all tasks in the workflow.

    This script requires that `airflow` be installed within the Python environment
    you are running this script in. It also requires importing of the training and
    monitoring modules.

    The script defines the dag and the tasks, and sets the order of tasks. Tasks, which
    use BashOperator, EmptyOperator, and PythonOperator are:

    task_start_dag, task_define_variables, task_initialize_vars, task_transform_data,
    task_define_variables, task_split_data, task_mlflow_search, task_find_best_params,
    task_run_best_model, task_register_best_model, task_test_model, task_compare_models,
    task_get_top_run, task_prepare_evidently_data, task_create_evidently_reports,
    task_evaluate_data_drift, task_record_metrics, task_monitor_evidently, and task_end_dag.
"""

# Import libraries
# from airflow.utils.dates import days_ago
from datetime import datetime, timedelta

from airflow.models import DAG
from airflow.operators.bash import BashOperator

# from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from monitoring.evidently_monitoring import (
    create_evidently_reports,
    evaluate_data_drift,
    monitor_evidently,
    prepare_evidently_data,
    record_metrics,
)
from training.data_preprocessor import split_data, transform_data
from training.data_processor import (
    compare_models,
    find_best_params,
    get_top_run,
    register_best_model,
    run_best_model,
    search_best_parameters,
    test_model,
)
from training.var_init import define_variables

MLFLOW_EXPERIMENT_NAME = "mlflow-experiment-1"
EVIDENTLY_EXPERIMENT_NAME = "evidently-experiment-1"
MODEL_NAME = "xgboost-model"
BUCKET_NAME = "s3b-tip-predictor"
KEY = "data/tips.csv"
CURRENT_DIR = "/home/ubuntu/Waiter-Tips-Prediction/"
TEST_SIZE = 0.2
TAG_MLFLOW = "xgboost"
TAG_EVIDENTLY = "evidently"
METRIC = "metrics.rmse ASC"
MAX_RESULTS = 5000


default_args = {
    "owner": "serdar",
    "start_date": datetime(2022, 8, 25, 2),  # days_ago(2)
    "end_date": datetime(2022, 12, 25, 2),
    "depends_on_past": False,
    "email": ["serdar@example.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(seconds=10),
}

with DAG(
    dag_id="waiter_tip_trainer_v1",
    default_args=default_args,
    description="Training dag for waiter tip prediction",
    schedule_interval="@monthly",  # "*/13 * * * *",
    dagrun_timeout=timedelta(minutes=60),
    catchup=False,
    tags=[TAG_MLFLOW],
) as dag:

    task_start_dag = EmptyOperator(
        task_id="start_dag",
    )

    task_define_variables = PythonOperator(
        task_id="define_variables",
        python_callable=define_variables,
        op_kwargs={
            "mlf_dict": {
                "mlflow_experiment_name": MLFLOW_EXPERIMENT_NAME,
                "evidently_experiment_name": EVIDENTLY_EXPERIMENT_NAME,
                "model_name": MODEL_NAME,
            },
            "s3_dict": {"bucket_name": BUCKET_NAME, "key": KEY},
            "local_dict": {"current_dir": CURRENT_DIR},
        },
        do_xcom_push=False,
    )

    task_initialize_vars = BashOperator(
        task_id="initialize_vars",
        bash_command="sleep 10",
        do_xcom_push=False,
    )

    task_transform_data = PythonOperator(
        task_id="transform_data",
        python_callable=transform_data,
        do_xcom_push=False,
    )

    task_split_data = PythonOperator(
        task_id="split_data",
        python_callable=split_data,
        op_kwargs={"test_size": TEST_SIZE},
        do_xcom_push=False,
    )

    task_mlflow_search = PythonOperator(
        task_id="search_best_parameters",
        python_callable=search_best_parameters,
        op_kwargs={"tag": TAG_MLFLOW},
        do_xcom_push=False,
    )

    task_find_best_params = PythonOperator(
        task_id="find_best_params",
        python_callable=find_best_params,
        op_kwargs={"metric": METRIC, "max_results": MAX_RESULTS},
    )

    task_run_best_model = PythonOperator(
        task_id="run_best_model",
        python_callable=run_best_model,
        op_kwargs={"tag": TAG_MLFLOW},
    )

    task_register_best_model = PythonOperator(
        task_id="register_best_model",
        python_callable=register_best_model,
        op_kwargs={
            "version_description": "This model version was built using XGBoost Regression."
        },
    )

    task_test_model = PythonOperator(
        task_id="test_model",
        python_callable=test_model,
    )

    task_compare_models = PythonOperator(
        task_id="compare_models",
        python_callable=compare_models,
        do_xcom_push=False,
    )

    task_get_top_run = PythonOperator(
        task_id="get_top_run",
        python_callable=get_top_run,
        op_kwargs={"metric": METRIC},
        do_xcom_push=False,
    )

    task_prepare_evidently_data = PythonOperator(
        task_id="prepare_evidently_data",
        python_callable=prepare_evidently_data,
        do_xcom_push=False,
    )

    task_create_evidently_reports = PythonOperator(
        task_id="create_evidently_reports",
        python_callable=create_evidently_reports,
        do_xcom_push=False,
    )

    task_evaluate_data_drift = PythonOperator(
        task_id="evaluate_data_drift",
        python_callable=evaluate_data_drift,
    )

    task_record_metrics = PythonOperator(
        task_id="record_metrics",
        python_callable=record_metrics,
        op_kwargs={"tag": TAG_EVIDENTLY},
        do_xcom_push=False,
    )

    task_monitor_evidently = PythonOperator(
        task_id="monitor_evidently",
        python_callable=monitor_evidently,
    )

    task_end_dag = EmptyOperator(
        task_id="end_dag",
    )

task_start_dag >> [task_define_variables, task_initialize_vars]
task_initialize_vars >> task_transform_data
[task_define_variables, task_transform_data] >> task_split_data >> task_mlflow_search
(
    task_mlflow_search
    >> task_find_best_params
    >> task_run_best_model
    >> task_register_best_model
)
task_register_best_model >> task_test_model >> task_compare_models >> task_get_top_run
(
    task_get_top_run
    >> task_prepare_evidently_data
    >> [task_create_evidently_reports, task_evaluate_data_drift]
)
(
    task_evaluate_data_drift
    >> [task_record_metrics, task_monitor_evidently]
    >> task_end_dag
)
