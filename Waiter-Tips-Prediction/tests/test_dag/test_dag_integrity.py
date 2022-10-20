"""
    This module tests dag integrity.

    This script requires that `pytest` and `airflow` be installed within the Python
    environment you are running this script in.

    This file contains the following functions:

        * test_dag_integrity - imports DAG files and checks for a valid DAG instance
        * _import_file - loads the module
"""

# Import libraries
import glob
from os import path
from types import ModuleType
from typing import Any

import pytest
from airflow import models as airflow_models
from airflow.utils.dag_cycle_tester import check_cycle

DAG_PATHS = glob.glob(path.join(path.dirname(__file__), "..", "..", "dags", "*.py"))


@pytest.mark.parametrize("dag_path", DAG_PATHS)
def test_dag_integrity(dag_path: Any) -> None:

    """
    Imports DAG files and checks for a valid DAG instance.
    """

    dag_name = path.basename(dag_path)
    module = _import_file(dag_name, dag_path)

    # Validate if there is at least 1 DAG object in the file
    dag_objects = [
        var for var in vars(module).values() if isinstance(var, airflow_models.DAG)
    ]
    assert dag_objects

    # For every DAG object, test for cycles
    for dag in dag_objects:
        check_cycle(dag)


def _import_file(module_name: str, module_path: str) -> ModuleType:

    """
    Loads the module.
    """

    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module
