---
name: generate-report
description: Generates professional and well-structured reports from various data formats based on user instructions.
---

# Generate Report

## Objective
To create a clear, professional, and well-structured report based on user-provided data and instructions.

## User-Provided Inputs
- **Topic/Goal:** The purpose of the report and the key questions to be answered.
- **Data:** The data to be analyzed, provided as a file (CSV, JSON, etc.), a code block (Python dictionary, list of lists), or a reference to a known dataset.
- **Specific Requirements:** Any specific sections, analyses, visualizations, or metrics to include.
- **Audience:** The intended audience for the report (e.g., technical experts, business executives, general public).
- **Output Format:** The desired final format for the report (e.g., Markdown, text).

## Steps

### Step 1: Deconstruct the Request & Clarify Scope
1.  Acknowledge the user's request to generate a report.
2.  Identify and confirm the following key parameters from the user's prompt:
    - **Primary Goal:** What is the main question the report should answer or the story it should tell?
    - **Intended Audience:** Who will be reading this report? This will influence the tone, language, and level of detail.
    - **Data Source:** Where is the data coming from and in what format?
    - **Required Content:** Are there any specific sections, analyses, or visualizations that must be included?
    - **Desired Format:** What is the final output format (e.g., Markdown)?
3.  If any of this information is missing or unclear, ask clarifying questions before proceeding.
    - *Example:* "This sounds like an interesting report. To make sure I tailor it correctly, could you tell me who the intended audience is? Are they technical experts or business stakeholders?"
    - *Example:* "I see the data file. Are there any specific charts or tables you would like me to generate from it?"

### Step 2: Ingest and Analyze the Data
1.  Access the data provided by the user. Use the `code_interpreter` to load and inspect the data.
    - For files: `pd.read_csv()`, `pd.read_json()`, `json.load()`, etc.
    - For code blocks: Parse the data structure directly.
2.  Perform an initial Exploratory Data Analysis (EDA) to understand the dataset.
    - Display the first few rows (`.head()`).
    - Check data types, column names, and for missing values (`.info()`).
    - Calculate basic descriptive statistics (`.describe()`).
3.  Summarize your initial findings about the data's structure, quality, and key statistics for the user. This confirms you are on the right track before deep analysis.
4.  Perform the primary data analysis required to meet the report's goal. This may include:
    - Filtering, sorting, and grouping data based on user requirements.
    - Calculating aggregations (sums, averages, counts, etc.).
    - Identifying trends, patterns, correlations, or significant anomalies.
    - Generating clear and relevant visualizations (bar charts, line graphs, scatter plots) using libraries like Matplotlib or Seaborn. Save any generated plots as image files.

### Step 3: Structure and Draft the Report
1.  Propose a clear and logical structure for the report to the user. If the user did not provide one, suggest a standard, effective structure:
    - **Title:** A concise and descriptive title.
    - **Executive Summary:** A brief, high-level overview of the most critical findings and recommendations. (Note: Write this section *last*, but place it *first*).
    - **Introduction:** State the report's purpose, scope, and objectives.
    - **Data Overview:** Briefly describe the data source and any relevant data preparation steps.
    - **Analysis & Findings:** The main body of the report. Present the results of your analysis from Step 2. Embed tables and visualizations where appropriate to support your points. Structure this section thematically around the key questions of the report.
    - **Conclusion & Recommendations:** Summarize the key takeaways and suggest next steps or actionable insights based on the findings.
2.  Once the structure is approved, begin drafting the content for each section.
3.  Write in a clear, professional tone suitable for the target audience. Use headings, subheadings, bullet points, and bold text to improve readability.
4.  Ensure that every finding, claim, or recommendation is directly supported by the data analysis you performed. Reference specific tables or charts (e.g., "As shown in Table 1...", "Figure 2 illustrates a clear upward trend...").

### Step 4: Review and Finalize
1.  Present the complete first draft of the report to the user in the agreed-upon format.
2.  Explicitly ask for feedback and revisions.
    - *Example:* "Here is the draft of the report. Please review it and let me know if you'd like any changes to the content, structure, or tone."
3.  Carefully incorporate any requested revisions. If a requested change conflicts with the data, explain the discrepancy professionally.
4.  Provide the final, polished report to the user.