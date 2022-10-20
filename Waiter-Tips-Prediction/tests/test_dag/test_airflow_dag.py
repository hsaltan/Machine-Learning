"""
    This module performs tests for the dag and task dependencies.

    This script requires that `pytest` and `airflow` be installed within the Python
    environment you are running this script in.

    The script checks the dag tags if any, the tasks involved, the number of tasks,
    downstream and upstream dependencies between them.

    This file contains the following functions:

        * dag_bag - sets the dagbag as a fixture for repetitive use
        * the_dag - sets the dag as a fixture for repetitive use
        * test_dagbag - tests for dag integrity
        * test_tag - tests the dag if any tags exist
        * test_task_count - tests for dag definition, checking the number of tasks in the dag
        * test_contain_tasks - tests the dag for checking the tasks it contains
        * test_dependencies - tests the dag for checking dependencies between tasks
"""

# Import libraries
from typing import Any

import pytest
from airflow.models import DagBag


@pytest.fixture
def dag_bag() -> Any:

    """
    Sets the dagbag as a fixture for repetitive use.
    """

    dagbag = DagBag(include_examples=False)

    return dagbag


@pytest.fixture
def the_dag(dag_bag: Any) -> Any:

    """
    Sets the dag as a fixture for repetitive use.
    """

    dag_id = "waiter_tip_trainer_v1"
    dag = dag_bag.get_dag(dag_id)

    return dag


def test_dagbag(dag_bag: Any) -> None:

    """
    Tests for dag integrity.
    """

    assert not dag_bag.import_errors


def test_tag(the_dag: Any) -> None:

    """
    Tests the dag if any tags exist.
    """

    assert the_dag.tags


# Dag definition
def test_task_count(the_dag: Any) -> None:

    """
    Test for dag definition, checking the number of tasks
    in the dag.
    """

    assert len(the_dag.tasks) == 18


def test_contain_tasks(the_dag: Any) -> None:

    """
    Tests the dag for checking the tasks it contains.
    """

    tasks = the_dag.tasks
    task_ids = list(map(lambda task: task.task_id, tasks))
    assert sorted(task_ids) == sorted(
        [
            "start_dag",
            "define_variables",
            "initialize_vars",
            "transform_data",
            "split_data",
            "search_best_parameters",
            "find_best_params",
            "run_best_model",
            "register_best_model",
            "test_model",
            "compare_models",
            "get_top_run",
            "prepare_evidently_data",
            "create_evidently_reports",
            "evaluate_data_drift",
            "record_metrics",
            "monitor_evidently",
            "end_dag",
        ]
    )


def test_dependencies(the_dag: Any) -> None:

    """
    Tests the dag for checking dependencies between tasks.
    """

    task_mlflow_search = the_dag.get_task("search_best_parameters")
    task_split_data = the_dag.get_task("split_data")
    task_create_evidently_reports = the_dag.get_task("create_evidently_reports")
    task_prepare_evidently_data = the_dag.get_task("prepare_evidently_data")

    upstream_task_ids_1 = list(
        map(lambda task: task.task_id, task_mlflow_search.upstream_list)
    )
    assert ["split_data"] == upstream_task_ids_1

    upstream_task_ids_2 = list(
        map(lambda task: task.task_id, task_split_data.upstream_list)
    )
    assert sorted(["define_variables", "transform_data"]) == sorted(upstream_task_ids_2)

    downstream_task_ids_1 = list(
        map(lambda task: task.task_id, task_create_evidently_reports.downstream_list)
    )
    assert not downstream_task_ids_1

    downstream_task_ids_2 = list(
        map(lambda task: task.task_id, task_prepare_evidently_data.downstream_list)
    )
    assert sorted(["create_evidently_reports", "evaluate_data_drift"]) == sorted(
        downstream_task_ids_2
    )
