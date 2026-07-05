---
name: project-initializer
description: Converts project initialization requests into a JSON command for runtime/project_initializer.py.
---

# Project Initializer

This skill processes a user's project initialization request and generates a JSON command to execute `runtime/project_initializer.py`.

## Input Request Parsing Rules

The user's project initialization request will be parsed according to these rules:

1.  **Project Name (`project_name`):**
    *   Attempt to extract a project name by looking for explicit indicators such as "project named [NAME]", "project [NAME]", "application [NAME]", or "app [NAME]".
    *   If no explicit name is found, attempt to infer it from context, prioritizing the first capitalized word following keywords like "create", "initialize", or "make".
    *   If no project name can be reliably extracted, default to "MyProject".

2.  **Project Root (`project_root`):**
    *   Default value is `/kaggle/working`.
    *   Override the default if the user explicitly specifies a root path using phrases like "in [PATH]", "at [PATH]", or "root [PATH]".

3.  **Directories (`directories`):**
    *   Extract directory names explicitly mentioned in the request using phrases such as "with directories [DIR1], [DIR2], ...", "folders [DIR1] and [DIR2]", or "create [DIR1], [DIR2]".
    *   If no directories are specified, use the default set: `['src', 'tests']`.
    *   Ensure all collected directory names are unique by removing any duplicates.

## Output Format

The skill will always produce a single JSON object with the following structure:


```json
{
  "name": "run_python_script",
  "script": "runtime/project_initializer.py",
  "args": {
    "project_name": "<extracted_or_default_project_name>",
    "project_root": "<extracted_or_default_project_root>",
    "directories": ["<unique_directory_name_1>", "<unique_directory_name_2>", "..."]
  }
}
```


The `args` field will always be a JSON object. Only the values within `args` will vary based on the user's request; the structure of the JSON object itself, including `name` and `script` fields, will remain constant.

## Usage Example

**User Request:** "Initialize a new web app called MyWebApp in /home/user/projects with folders for models, views, and controllers."

**Expected JSON Output:**

```json
{
  "name": "run_python_script",
  "script": "runtime/project_initializer.py",
  "args": {
    "project_name": "MyWebApp",
    "project_root": "/home/user/projects",
    "directories": ["models", "views", "controllers"]
  }
}
```