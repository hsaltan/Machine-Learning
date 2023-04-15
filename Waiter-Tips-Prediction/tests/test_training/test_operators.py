"""
    This module performs tests for functions in the training module.

    This script requires that `pytest`, `mlflow` and `airflow` be installed within the
    Python environment you are running this script in. It also requires importing of the
    training module.

    The script goes over many functions that are in var_init, data_preprocessor, and
    data_processor modules to test their working. The test includes BashOperator,
    PythonOperator, and Variables in Airflow.

    This file contains the following functions:

        * the_dag - sets the dag as a fixture for repetitive use
        * test_bash_operator - tests the bash operator
        * test_transform_data - tests importing data from the S3 bucket, converting it into
        a pandas dataframe, and making necessary transformations
        * test_split_data - tests splitting the data as training and validation sets, and
        saving them to the local disk and to the S3 bucket
        * test_define_variables - tests defining variables on Airflow
        * test_search_best_parameters - tests searching and finding the optimum parameters
        within the defined ranges with Hyperopt
        * test_get_experiments_by_id - tests listing all existing experiments and finding their ids
        * test_get_top_run - tests checking all runs in all experiments and finding the
        best run that returns the lowest loss value
"""

# Import libraries
from datetime import datetime
from typing import Any

import pytest
from airflow.models import DAG, Variable
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from mlflow.tracking import MlflowClient

from dags.training.data_preprocessor import split_data, transform_data
from dags.training.data_processor import (
    get_experiments_by_id,
    get_top_run,
    search_best_parameters,
)
from dags.training.var_init import define_variables

mlflow_client = MlflowClient("http://127.0.0.1:5000")


@pytest.fixture
def the_dag() -> Any:

    """
    Sets the dag as a fixture for repetitive use.
    """

    dag = DAG(dag_id="waiter_tip_trainer_v1", start_date=datetime(2022, 8, 25, 2))

    return dag


def test_bash_operator(the_dag: Any) -> None:

    """
    Tests the bash operator.
    """

    test = BashOperator(
        dag=the_dag, task_id="initialize_vars", bash_command="echo hello"
    )
    result = test.execute(context={})

    assert result == "hello"


def test_transform_data(the_dag: Any) -> None:

    """
    Tests importing data from the S3 bucket, converting it into
    a pandas dataframe, and making necessary transformations.
    """

    task = PythonOperator(
        dag=the_dag, task_id="transform_data", python_callable=transform_data
    )
    result = task.execute(context={})

    local_dict = {
        "current_dir": "/home/ubuntu/app/Waiter-Tips-Prediction/",
        "local_data_transformed_filename": "/home/ubuntu/app/Waiter-Tips-Prediction/data/tips_transformed.csv",
    }
    bucket_name = "s3b-tip-predictor"

    assert result[0] == local_dict
    assert result[1] == bucket_name
    assert result[2] == 2
    assert result[3] == 3
    assert result[4] == 1


def test_split_data(the_dag: Any) -> None:

    """
    Tests splitting the data as training and validation sets, and
    saving them to the local disk and to the S3 bucket.
    """

    task = PythonOperator(dag=the_dag, task_id="split_data", python_callable=split_data)
    result = task.execute(context={"test_size": 0.25})

    assert result[0] == 183
    assert result[1] == 61
    assert result[0] + result[1] == 244


def test_define_variables(the_dag: Any) -> None:

    """
    Tests defining variables on Airflow.
    """

    params = {
        "mlf_dict": {
            "mlflow_experiment_name": "mlflow-experiment-1",
            "evidently_experiment_name": "evidently-experiment-1",
            "model_name": "xgboost-model",
        },
        "s3_dict": {"bucket_name": "s3b-tip-predictor", "key": "data/tips.csv"},
        "local_dict": {"current_dir": "/home/ubuntu/app/Waiter-Tips-Prediction/"},
    }

    task = PythonOperator(
        dag=the_dag, task_id="define_variables", python_callable=define_variables
    )
    result = task.execute(context={**params})

    # Input variables for cross-check
    bucket_name = params["s3_dict"]["bucket_name"]
    key = params["s3_dict"]["key"]

    # Retrieve the stored variables from Airflow
    s3_dict = Variable.get("s3_dict", deserialize_json=True)
    s3_bucket = s3_dict["bucket_name"]
    s3_key = s3_dict["key"]

    assert isinstance(result[0], str) is True
    assert isinstance(result[1], str) is True
    assert isinstance(result[2], str) is True
    assert result[0] == "mlflow-experiment-1"
    assert result[1] == "evidently-experiment-1"
    assert result[2] == "xgboost-model"
    assert bucket_name == s3_bucket
    assert key == s3_key


def test_search_best_parameters(the_dag: Any) -> None:

    """
    Tests searching and finding the optimum parameters within the
    defined ranges with Hyperopt.
    """

    import math

    task = PythonOperator(
        dag=the_dag,
        task_id="search_best_parameters",
        python_callable=search_best_parameters,
    )
    result = task.execute(context={"tag": "test_xgboost"})

    # Float values may differ, so it makes sense to check equality with tolerance
    assert isinstance(result["learning_rate"], float) is True
    assert math.isclose(round(float(result["subsample"]), 2), 0.80, abs_tol=0.2) is True


def test_get_experiments_by_id() -> None:

    """
    Tests listing all existing experiments and finding their ids.
    """

    # IDs of existing experiments
    experiment_ids = get_experiments_by_id()

    assert not "0" in experiment_ids
    assert "1" in experiment_ids


def test_get_top_run(the_dag: Any) -> None:

    """
    Tests checking all runs in all experiments and finding the
    best run that returns the lowest loss value.
    """

    import math

    task = PythonOperator(
        dag=the_dag, task_id="get_top_run", python_callable=get_top_run
    )
    result = task.execute(context={"metric": "metrics.rmse ASC"})

    # Float values may differ, so it makes sense to check equality with tolerance
    assert result["experiment_id"] == "1"
    assert isinstance(result["best_run_id"], str) is True
    assert (
        math.isclose(round(float(result["best_run_rmse"]), 4), 0.8100, abs_tol=0.1)
        is True
    )
