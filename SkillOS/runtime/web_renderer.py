
from typing import Any
from pathlib import Path
from IPython.display import HTML, display


def generate_webpage(
    command: dict[str, Any],
) -> list[str]:
    """
    Save generated web source files and display the main HTML page.

    Args
    ----
    command:
        Dictionary containing:
        - generated_files: dict mapping filenames to file contents
        - output_folder: folder where files will be saved
        - main_file: HTML file to display, usually "index.html"

    Returns
    -------
    list[str]
        File paths of all saved files.
    """

    generated_files: dict[str, str] = command["generated_files"]

    output_folder = Path(
        command.get("output_folder", "/kaggle/working/web_output")
    )

    main_file = command.get("main_file", "index.html")

    output_folder.mkdir(parents=True, exist_ok=True)

    saved_paths: list[str] = []

    for filename, content in generated_files.items():
        file_path = output_folder / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        saved_paths.append(str(file_path))

    main_path = output_folder / main_file

    if not main_path.exists():
        raise FileNotFoundError(f"Main HTML file not found: {main_path}")

    html = main_path.read_text(encoding="utf-8")

    display(
        HTML(
            f"""
            <div style="
                width: 98vw;
                min-height: 1000px;
                margin: 0 auto;
                overflow: auto;
            ">
                {html}
            </div>
            """
        )
    )

    return saved_paths
