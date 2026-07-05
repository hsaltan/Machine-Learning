
from pathlib import Path
from typing import Any


def initialize_project(
    command: dict[str, Any],
) -> str:
    """
    Create a new project directory and its initial subdirectories.

    Description
    -----------
    Creates the requested project folder under the specified project
    root and generates all required subdirectories. Existing
    directories are preserved.

    Args
    ----
    command:
        Dictionary containing the project initialization parameters.

        Expected structure:

        {
            "args": {
                "project_root": "...",
                "project_name": "...",
                "directories": [...]
            }
        }

    Returns
    -------
    str

        Absolute path of the created project directory.

    Raises
    ------
    KeyError

        If one or more required arguments are missing.

    Example
    -------
    >>> initialize_project(command)
    '/kaggle/working/project-catflix'
    """

    # -----------------------------------------------------
    # Read command arguments
    # -----------------------------------------------------

    args = command["args"]

    project_root = Path(
        args["project_root"]
    )

    project_name = args["project_name"]

    directories = args["directories"]

    # -----------------------------------------------------
    # Create the project directory
    # -----------------------------------------------------

    project_dir = project_root / project_name

    project_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -----------------------------------------------------
    # Create the requested subdirectories
    # -----------------------------------------------------

    for directory in directories:

        (project_dir / directory).mkdir(
            parents=True,
            exist_ok=True,
        )

    # -----------------------------------------------------
    # Return the project path
    # -----------------------------------------------------

    return str(project_dir)
