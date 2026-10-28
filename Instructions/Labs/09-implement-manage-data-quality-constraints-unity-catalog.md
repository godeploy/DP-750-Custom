---
lab:
  index: 09
  title: Implement and Manage Data Quality Constraints in Unity Catalog
  module: Implement and manage data quality constraints in Unity Catalog
  module-url: https://learn.microsoft.com/training/modules/implement-manage-data-quality-constraints-unity-catalog/
  notebook: https://github.com/MicrosoftLearning/DP-750T00-Implement-Data-Engineering-Solutions-using-Azure-Databricks/blob/main/Allfiles/09-implement-manage-data-quality-constraints-unity-catalog.ipynb
  description: In this lab, you build a Lakeflow Spark Declarative Pipeline for ClearCover Insurance that enforces data quality constraints on raw claims data. You implement nullability and range checks using pipeline expectations, validate data types with col().cast(), and handle schema drift using Auto Loader's rescued data column. You then create and run the pipeline in the Databricks UI and monitor data quality metrics.
  duration: 45 minutes
  level: 300
  islab: true
  primarytopics:
    - Azure Databricks
---

# Lab 09: Implement and Manage Data Quality Constraints in Unity Catalog

## Introduction

You are a data engineer at **ClearCover Insurance**, a fictional insurance provider. Each day, raw claims data arrives from regional offices and partner brokers. Unfortunately, the data is inconsistent: some records are missing required identifiers, claim amounts are formatted as strings or carry negative values, dates are occasionally malformed, and the source schema may silently gain new columns over time.

Your mission is to build a **Lakeflow Spark Declarative Pipeline** that enforces data quality constraints at every layer of the pipeline — catching bad records before they reach actuarial models and reporting dashboards.

You work through the following exercises:

| Exercise   | Topic                                                    |
| ---------- | -------------------------------------------------------- |
| Exercise 1 | Set up the ClearCover Insurance Data Platform (notebook) |
| Exercise 2 | Explore data quality issues in Catalog Explorer          |
| Exercise 3 | Implement nullability and status validation              |
| Exercise 4 | Add data type checks using col().cast()                  |
| Exercise 5 | Handle schema drift with rescued data                    |
| Exercise 6 | Run and monitor the pipeline                             |

---

## 🤖 Genie Code — Use it always

Throughout every exercise in this lab, you are **expected and encouraged to use Genie Code**. Every exercise includes a suggested prompt to get you started. Genie Code is your pair programmer — use it to generate code, understand errors, and explore alternatives.

To open Genie Code, select the ![assistant-icon](https://raw.githubusercontent.com/MicrosoftLearning/DP-750T00-Implement-Data-Engineering-Solutions-using-Azure-Databricks/refs/heads/main/Allfiles/media/genie-code.svg) on the right side of any notebook cell, or use the keyboard shortcut.
---

## 🔑 Lab environment note: your personal catalog

In this lab environment, several students share one Unity Catalog metastore, and a catalog name can only exist once in a metastore. To keep your work separate, the lab notebook adds your personal **lab ID** (8 characters, for example `1a2b3c4d`) to the catalog name, so this lab's `insurance_lab` catalog is called **`insurance_lab_<lab ID>`** for you.

- The first code cell in the notebook prints your lab ID and catalog name. **Write them down** — your lab ID is the same in every lab.
- Wherever these instructions show `<lab ID>`, replace it with your own lab ID.
- If your notebook session restarts (for example after a break) and you see *SCHEMA_NOT_FOUND* or *TABLE_OR_VIEW_NOT_FOUND* errors, run the notebook's setup cell again.

---

## Prerequisites

- An **Azure Databricks Premium workspace** provisioned using [Lab 00: Set up your Azure Databricks environment](00-setup.md).
- You are familiar with basic Python and PySpark concepts.
- You have completed the earlier labs in this learning path (or are comfortable with Unity Catalog basics).

---

## Importing the Setup Notebook

1. In the Databricks workspace, click **Workspace** in the left sidebar.
2. Navigate to or create a folder where you want to store the lab.
3. Click the **⋮** (kebab) menu or right-click the folder, then select **Import**.
4. Choose **URL**, enter the following URL, and click **Import**:
   `{{FILES_BASE_URL}}/Allfiles/09-implement-manage-data-quality-constraints-unity-catalog.ipynb`
5. Open the imported notebook and, in the compute selector at the top, choose **Serverless** compute.

---

## Exercise 1: Set up the ClearCover Insurance Data Platform

Run all cells in the setup notebook **09-implement-manage-data-quality-constraints-unity-catalog** from top to bottom.

The notebook creates the following objects:

| Object                                | Description                                                  |
| ------------------------------------- | ------------------------------------------------------------ |
| insurance_lab_<lab ID> catalog                 | Top-level namespace for the ClearCover Insurance platform    |
| insurance_lab_<lab ID>.bronze schema           | Raw, unprocessed claims data as received from source systems |
| insurance_lab_<lab ID>.silver schema           | Validated and type-safe records                              |
| insurance_lab_<lab ID>.gold schema             | Aggregated reporting data                                    |
| insurance_lab_<lab ID>.bronze.raw_files volume | Landing zone for raw CSV claim files                         |
| insurance_lab_<lab ID>.bronze.claims_raw table | Delta table with 20 raw claims records                       |

After the notebook completes, verify the objects in **Catalog Explorer** before continuing.

---

## Exercise 2: Explore Data Quality Issues

Before writing any pipeline code, explore the raw data to understand the quality problems you need to fix.

### Task 2.1: Query the raw claims table

Open a new SQL query editor (or a notebook cell) and run the following query. Replace `<lab ID>` with your lab ID — the SQL editor doesn't know your notebook's current catalog, so use the full name:

```sql
SELECT *
FROM insurance_lab_<lab ID>.bronze.claims_raw
ORDER BY claim_id NULLS LAST;
```

Review the results and find at least one row for each of the following issues:

| Issue                      | Column(s) to check                     |
| -------------------------- | -------------------------------------- |
| Missing primary identifier | claim_id or customer_id is NULL        |
| Unparseable date           | claim_date contains a non-date string  |
| Unparseable amount         | claim_amount contains N/A or is empty  |
| Negative amount            | claim_amount is a negative number      |
| Invalid status             | status is not OPEN, PENDING, or CLOSED |

### Task 2.2: Inspect the schema

Run the following to confirm that claim_date and claim_amount are stored as STRING:

```sql
DESCRIBE TABLE insurance_lab_<lab ID>.bronze.claims_raw;
```

These columns are intentionally strings in the bronze layer. The pipeline exercises will enforce the correct types during ingestion into silver.

---

## Exercise 3: Nullability and Status Validation

### Task 3.0: Create the ETL pipeline and import the pipeline file

Before writing any pipeline code, import the starter pipeline file and create the Lakeflow Spark Declarative Pipeline in Databricks.

**Import the pipeline file:**

1. In the Databricks workspace, click **Workspace** in the left sidebar.
2. Navigate to the folder where you stored the lab notebook.
3. Click the **⋮** (kebab) menu or right-click the folder, then select **Import**.
4. Choose **URL**, enter the following URL, and click **Import**:
   `{{FILES_BASE_URL}}/Allfiles/09-implement-manage-data-quality-constraints.py`
5. The file appears in your workspace as a Python source file — note its path for the next step.

**Create the pipeline:**

1. In the Databricks workspace left sidebar, click **Jobs & Pipelines**.
2. Click **Create ETL pipeline** (Python).
3. Click the **gear (⚙️) icon** to open the pipeline settings dialog, then configure the pipeline with the following settings:

   | Setting        | Value                                  |
   | -------------- | -------------------------------------- |
   | Pipeline name  | **ClearCover Claims Quality Pipeline** |
   | Pipeline mode  | **Triggered**                          |
   | Target catalog | **insurance_lab_<lab ID>**, schema **silver**   |
   | Compute        | **Serverless**                         |
   | Configuration  | key `lab_catalog`, value `insurance_lab_<lab ID>` |

   > **Why the configuration value?** The pipeline code reads `lab_catalog` to find your tables and your volume, so it works with your personal catalog. Add it in the **Configuration** section of the pipeline settings (select **Add configuration**; in some versions it's under **Advanced**). Type your real catalog name, for example `insurance_lab_1a2b3c4d`.

4. In the pipeline editor, locate the **left pane** (asset browser). Open its menu and select **Import**, then browse to your imported `09-implement-manage-data-quality-constraints.py` file to add it as the pipeline source code.

Open the imported pipeline file and keep it open throughout exercises 3–5. You will now edit it to add data quality constraints.

### Task 3.1: Add nullability and status expectations to claims_validated()

Open 09-implement-manage-data-quality-constraints.py and add the following expectations to the *claims_validated()* function. Place all decorators between `@dp.table(...)` and `def claims_validated():`.

| Expectation name  | Condition                                 | Action        |
| ----------------- | ----------------------------------------- | ------------- |
| valid_claim_id    | `claim_id IS NOT NULL`                    | Drop          |
| valid_customer_id | `customer_id IS NOT NULL`                 | Drop          |
| valid_status      | `status IN ('OPEN', 'PENDING', 'CLOSED')` | Warn (keep)   |
| valid_coverage    | `coverage_amount > 0`                     | Fail pipeline |

Use `@dp.expect_or_drop` to drop violating rows, `@dp.expect` to warn without dropping, and `@dp.expect_or_fail` to stop the pipeline on a violation.

> 🤖 **Ask Genie Code:**
> *"Show me how to use expect_or_drop, expect, and expect_or_fail decorators in a Lakeflow Spark Declarative Pipelines Python function"*

---

## Exercise 4: Data Type Checks

The claim_date and claim_amount columns arrive as strings. When `try_cast()` cannot parse a value, it returns NULL instead of raising an error. You can use that behaviour to identify and drop invalid records.

> **Why try_cast and not col().cast()?** With ANSI SQL mode — the default on serverless compute and current Databricks runtimes — a plain `cast()` of a value such as `not-a-date` raises an error and stops the whole pipeline. `try_cast()` returns NULL instead, so your expectations can drop the bad rows.

### Task 4.1: Apply try_cast() inside claims_validated()

Inside the claims_validated() function body, **before the return statement**, add two withColumn calls:

1. Convert claim_date from STRING to DATE using `expr('try_cast(claim_date AS date)')`
2. Convert claim_amount from STRING to DECIMAL(12,2) using `expr('try_cast(claim_amount AS decimal(12,2))')`

`expr` is already imported at the top of the pipeline file. Chain the two `withColumn` calls onto the `spark.readStream.table(...)` call that the function returns.

The transformed columns replace the originals, so downstream expectations and consumers see typed values.

> 🤖 **Ask Genie Code:**
> *"In PySpark, use withColumn and expr('try_cast(...)') to convert a streaming dataframe column from STRING to DATE type, and another column from STRING to DECIMAL(12,2). Show me the full withColumn syntax."*

### Task 4.2: Drop records with unparseable dates

After the cast in task 4.1, any row where claim_date is still NULL had an invalid original value. Add an `@dp.expect_or_drop` decorator to drop these rows:

```
expectation name: valid_claim_date
condition:        claim_date IS NOT NULL
```

### Task 4.3: Drop records with unparseable or missing amounts

Similarly, drop rows where claim_amount could not be cast:

```
expectation name: valid_claim_amount
condition:        claim_amount IS NOT NULL
```

### Task 4.4: Drop records with negative claim amounts

A negative claim amount is invalid in any insurance context. Drop these rows:

```
expectation name: non_negative_amount
condition:        claim_amount >= 0
```

> 💡 **Hint:** Place all expectation decorators between @dp.table(...) and def claims_validated():. Their order does not affect the result — all expectations are evaluated on each row.

> 🤖 **Ask Genie Code:**
> *"I'm using Lakeflow Spark Declarative Pipelines in Python. After applying try_cast to convert a column from STRING to DATE, which expectation condition do I use to drop rows where the cast failed?"*

---

## Exercise 5: Handle Schema Drift with Rescued Data

ClearCover receives claims files from several partner brokers. Occasionally a broker adds extra columns — such as broker_reference or fraud_score — without prior notice. Rather than crashing the pipeline when this happens, you want to capture unexpected data in a separate column for investigation.

### Task 5.1: Implement Auto Loader with rescue schema evolution mode

Complete the claims_rescued() function in 09-implement-manage-data-quality-constraints.py.

Use spark.readStream with Auto Loader (cloudFiles format) to read CSV files from your volume:

```
/Volumes/insurance_lab_<lab ID>/bronze/raw_files/
```

In the pipeline file this path is already stored in the variable `VOLUME_PATH`, so use `VOLUME_PATH` in your code rather than typing the path.

Configure it with the following options:

| Option                         | Value                                           |
| ------------------------------ | ----------------------------------------------- |
| cloudFiles.format              | csv                                             |
| header                         | true                                            |
| cloudFiles.schemaLocation      | f'{VOLUME_PATH}/_schema' (that is, /Volumes/insurance_lab_<lab ID>/bronze/raw_files/_schema) |
| cloudFiles.schemaEvolutionMode | rescue                                          |
| rescuedDataColumn              | _rescued_data                                   |
| cloudFiles.inferColumnTypes    | true                                            |

Remove the **pass** statement and return the configured readStream.

> 🤖 **Ask Genie Code:**
> *"Write a complete PySpark Auto Loader readStream block using cloudFiles format CSV with schemaEvolutionMode rescue and a _rescued_data column. Explain what each option does."*

> 💡 **Hint:** When the source file matches the expected schema, _rescued_data will be NULL for every row. If a future file adds new columns (like fraud_score), their values are captured as JSON in _rescued_data instead of breaking the pipeline.

---

## Exercise 6: Run and Monitor the Pipeline

With the pipeline code complete, run the pipeline you created in Exercise 3.

### Task 6.1: Save your pipeline file

Make sure you have saved all changes to 09-implement-manage-data-quality-constraints.py in the workspace editor before continuing.

### Task 6.2: Run the pipeline

Click **Start** to trigger a full pipeline run. Wait for the run to complete.

Observe the pipeline DAG in the graph view. You should see three dataset nodes:
- silver.claims_validated
- silver.claims_rescued
- gold.claims_summary

### Task 6.3: Monitor data quality metrics

1. In the pipeline graph, click the **claims_validated** dataset node.
2. In the right-hand panel, open the **Data quality** tab.
3. Review the expectation results and answer the following:
   - Which expectations **dropped** records, and how many?
   - Which expectation issued **warnings** (kept records but logged violations)?
   - Did valid_coverage trigger a **fail**? If so, this indicates a row in the source with `coverage_amount <= 0` — investigate which row caused it.

> 💡 **Hint:** If valid_coverage fails the pipeline, examine insurance_lab_<lab ID>.bronze.claims_raw for rows where coverage_amount is zero or NULL. The error message in the pipeline event log will also show the violating record.

### Task 6.4: Query the output tables

Run the following queries to verify the pipeline output (replace `<lab ID>` with your lab ID):

```sql
-- How many claims made it through all validations?
SELECT COUNT(*) AS valid_claim_count
FROM insurance_lab_<lab ID>.silver.claims_validated;

-- What types and statuses appear in the validated silver layer?
SELECT claim_type, status, COUNT(*) AS count
FROM insurance_lab_<lab ID>.silver.claims_validated
GROUP BY claim_type, status
ORDER BY claim_type, status;

-- Review the gold summary
SELECT *
FROM insurance_lab_<lab ID>.gold.claims_summary
ORDER BY claim_type, status;

-- Did Auto Loader capture any rescued data?
SELECT claim_id, _rescued_data
FROM insurance_lab_<lab ID>.silver.claims_rescued
WHERE _rescued_data IS NOT NULL;
```

> 🤖 **Ask Genie Code:**
> *"Looking at the counts in insurance_lab_<lab ID>.bronze.claims_raw vs insurance_lab_<lab ID>.silver.claims_validated, explain what each row reduction tells me about the data quality issues in the bronze data."*

---

## Clean Up (Optional)

To remove all lab resources when you are done:

```sql
DROP CATALOG IF EXISTS insurance_lab_<lab ID> CASCADE;
```
