---
name: web-file-generator
description: Converts web application requests into a JSON command for execution by runtime/web_renderer.py.
---

# Web File Generator

This skill specializes in converting a user's web application requirements into a complete set of production-quality source files packaged as a single JSON command. The resulting JSON is designed to be executed by the `runtime/web_renderer.py` script.

## Objectives
- Generate standards-compliant HTML5, CSS3, and JavaScript code.
- Ensure the application is responsive and functionally complete based on the user request.
- Package all generated files into a specific JSON structure without any surrounding text or markdown formatting.

## Process
1. **Analyze Requirements**: Carefully review the user's request for functionality, layout, and design preferences.
2. **Develop Source Code**:
    - **HTML**: Create semantic HTML5 structures.
    - **CSS**: Implement modern CSS3 (Flexbox/Grid) to ensure responsiveness and a professional look.
    - **JavaScript**: Write clean, efficient vanilla JS or specified libraries to handle the application logic.
3. **Package as JSON**: Organize the files into a single JSON object with the following schema:
    - `name`: Always set to `"run_python_script"`.
    - `script`: Always set to `"runtime/web_renderer.py"`.
    - `output_folder`: Use the user-specified path, or default to `"/kaggle/working/web_output"`.
    - `main_file`: The filename of the primary entry point (e.g., `"index.html"`).
    - `generated_files`: An object where keys are filenames and values are the full string contents of those files.

## Output Requirements
- The final output must be **ONLY** the raw JSON object.
- Do **NOT** include:
    - Markdown code blocks (e.g., no \`\`\`json).
    - Explanations or introductory text.
    - Closing remarks or status updates.
- The JSON must be valid and ready for programmatic parsing.

## Example JSON Structure
```json
{
  "name": "run_python_script",
  "script": "runtime/web_renderer.py",
  "output_folder": "/kaggle/working/web_output",
  "main_file": "index.html",
  "generated_files": {
    "index.html": "<html>...</html>",
    "style.css": "body { ... }",
    "script.js": "console.log('Hello');"
  }
}
```