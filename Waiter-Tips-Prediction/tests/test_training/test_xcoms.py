"""
    This module performs tests for XCom operations between functions.

    This script requires that `pytest` and `airflow` be installed within the Python
    environment you are running this script in.

    The script checks XCom push and pull operations between functions in the training
    and monitoring modules, excluding functions that have no XCom connection. Those
    tested functions are find_best_params, run_best_model, register_best_model, test_model,
    compare_models, evaluate_data_drift, and record_metrics.

    This file contains the following functions:

        * dag_bag - Sets the dagbag as a fixture for repetitive use
        * the_dag - Sets the dag as a fixture for repetitive use
        * test_xcoms_best_params - Checks the XCom variable for the best params
        * test_xcoms_best_run_id - Checks the XCom variable for the best run id
        * test_xcoms_model_details - Checks the XCom variable for the model details
        * test_xcoms_rmses - Checks the XCom variable for the RMSEs
        * test_xcoms_drifts - Checks the XCom variable for data drifts
"""

# Import libraries
import math
from typing import Any

import pytest
from airflow.models import DagBag
from airflow.models.taskinstance import TaskInstance


@pytest.fixture
def dag_bag() -> Any:

    """
    Sets the dagbag as a fixture for repetitive use.
    """

    dag_bag = DagBag(include_examples=False)

    return dag_bag


@pytest.fixture
def the_dag(dag_bag: Any) -> Any:

    """
    Sets the dag as a fixture for repetitive use.
    """

    dag_id = "waiter_tip_trainer_v1"
    dag = dag_bag.get_dag(dag_id)

    return dag


def test_xcoms_best_params(the_dag: Any) -> None:

    """
    Checks the XCom variable for the best params.
    """

    # Get the push and pull tasks of the dag
    push_to_xcoms_task = the_dag.get_task("find_best_params")
    pull_from_xcoms_task = the_dag.get_task("run_best_model")

    # Set the run_id for which to check the relevant xcom value.
    run_id = "manual__2022-09-20T08:52:33.473203+00:00"

    # Run the push task and push the variable to XCom
    push_to_xcoms_ti = TaskInstance(task=push_to_xcoms_task, run_id=run_id)
    context = push_to_xcoms_ti.get_template_context()
    push_to_xcoms_task.execute(context)

    # Run the pull task and pull the variable from XCom
    pull_from_xcoms_ti = TaskInstance(task=pull_from_xcoms_task, run_id=run_id)
    result = pull_from_xcoms_ti.xcom_pull(key="best_params")

    # Float values may differ, so it makes sense to check equality with tolerance
    assert float(result["colsample_bytree"]) == 0.3
    assert result["objective"] == "reg:squarederror"
    assert math.isclose(round(float(result["subsample"]), 2), 0.80, abs_tol=0.2) is True


def test_xcoms_best_run_id(the_dag: Any) -> None:

    """
    Checks the XCom variable for the best run id.
    """

    # Get the push and pull tasks of the dag
    push_to_xcoms_task = the_dag.get_task("run_best_model")
    pull_from_xcoms_task = the_dag.get_task("register_best_model")

    # Set the run_id for which to check the relevant xcom value.
    run_id = "manual__2022-09-20T08:52:33.473203+00:00"

    # Run the push task and push the variable to XCom
    push_to_xcoms_ti = TaskInstance(task=push_to_xcoms_task, run_id=run_id)
    context = push_to_xcoms_ti.get_template_context()
    push_to_xcoms_task.execute(context)

    # Run the pull task and pull the variable from XCom
    pull_from_xcoms_ti = TaskInstance(task=pull_from_xcoms_task, run_id=run_id)
    result = pull_from_xcoms_ti.xcom_pull(key="best_run_id")

    # Best run id is a hashed value for the run and changes for every run.
    # So, the below should never hold.
    assert isinstance(result, str) is True
    assert not result == "bestRunId"


def test_xcoms_model_details(the_dag: Any) -> None:

    """
    Checks the XCom variable for the model details.
    """

    # Get the push and pull tasks of the dag
    push_to_xcoms_task = the_dag.get_task("register_best_model")
    pull_from_xcoms_task = the_dag.get_task("test_model")

    # Set the run_id for which to check the relevant xcom value.
    run_id = "manual__2022-09-20T08:52:33.473203+00:00"

    # Run the push task and push the variable to XCom
    push_to_xcoms_ti = TaskInstance(task=push_to_xcoms_task, run_id=run_id)
    context = push_to_xcoms_ti.get_template_context()
    push_to_xcoms_task.execute(context)

    # Run the pull task and pull the variable from XCom
    pull_from_xcoms_ti = TaskInstance(task=pull_from_xcoms_task, run_id=run_id)
    result = pull_from_xcoms_ti.xcom_pull(key="model_details")

    # Model version increments by each run, take 1 step higher than the current
    # level to verify the version.
    assert result["model_name"] == "xgboost-model"
    assert result["model_version"] == "6"


def test_xcoms_rmses(the_dag: Any) -> None:

    """
    Checks the XCom variable for the RMSEs.
    """

    # Get the push and pull tasks of the dag
    push_to_xcoms_task = the_dag.get_task("test_model")
    pull_from_xcoms_task = the_dag.get_task("compare_models")

    # Set the run_id for which to check the relevant xcom value.
    run_id = "manual__2022-09-20T08:52:33.473203+00:00"

    # Run the push task and push the variable to XCom
    push_to_xcoms_ti = TaskInstance(task=push_to_xcoms_task, run_id=run_id)
    context = push_to_xcoms_ti.get_template_context()
    push_to_xcoms_task.execute(context)

    # Run the pull task and pull the variable from XCom
    pull_from_xcoms_ti = TaskInstance(task=pull_from_xcoms_task, run_id=run_id)
    result = pull_from_xcoms_ti.xcom_pull(key="rmses")

    # Float values may differ, so it makes sense to check equality with tolerance
    assert (
        math.isclose(
            round(float(result["model_production_rmse"]), 4), 0.8100, abs_tol=0.2
        )
        is True
    )
    assert (
        math.isclose(round(float(result["model_staging_rmse"]), 4), 0.8100, abs_tol=0.2)
        is True
    )


def test_xcoms_drifts(the_dag: Any) -> None:

    """
    Checks the XCom variable for data drifts.
    """

    # Get the push and pull tasks of the dag
    push_to_xcoms_task = the_dag.get_task("evaluate_data_drift")
    pull_from_xcoms_task = the_dag.get_task("record_metrics")

    # Set the run_id for which to check the relevant xcom value.
    run_id = "manual__2022-09-20T08:52:33.473203+00:00"

    # Run the push task and push the variable to XCom
    push_to_xcoms_ti = TaskInstance(task=push_to_xcoms_task, run_id=run_id)
    context = push_to_xcoms_ti.get_template_context()
    push_to_xcoms_task.execute(context)

    # Run the pull task and pull the variable from XCom
    pull_from_xcoms_ti = TaskInstance(task=pull_from_xcoms_task, run_id=run_id)
    result = pull_from_xcoms_ti.xcom_pull(key="drifts")

    # Float values may differ, so it makes sense to check equality with tolerance
    assert isinstance(result[2][0], str) is True
    assert math.isclose(result[2][1], 0.500, abs_tol=0.1) is True
    assert isinstance(result[2][2], bool) is True
