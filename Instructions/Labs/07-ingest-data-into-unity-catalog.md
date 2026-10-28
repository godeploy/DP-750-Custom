---
lab:
  index: 07
  title: Ingest data into Unity Catalog
  module: Ingest data into Unity Catalog
  module-url: https://learn.microsoft.com/training/modules/ingest-data-into-unity-catalog/
  notebook: https://github.com/MicrosoftLearning/DP-750T00-Implement-Data-Engineering-Solutions-using-Azure-Databricks/blob/main/Allfiles/07-ingest-data-into-unity-catalog.ipynb
  description: In this lab, you practise the core data ingestion techniques available in Azure Databricks. You load CSV files from a Unity Catalog managed volume into Delta tables using PySpark DataFrames, SQL COPY INTO, and CREATE TABLE AS SELECT. You also configure Auto Loader to automatically detect and process new files from cloud storage, demonstrating exactly-once ingestion for continuously arriving data.
  duration: 45 minutes
  level: 300
  islab: true
  primarytopics:
    - Azure Databricks
---

# Lab 07: Ingest Data into Unity Catalog

## Scenario

You are a data engineer at **Solaris Energy**, a renewable energy company operating solar farms in Spain and Germany, and wind turbine installations in the Netherlands and Denmark. Your team is building a centralised data platform on Azure Databricks to consolidate energy production readings, turbine maintenance events, and grid telemetry from all sites.

In this lab, you will practise the core data ingestion techniques available in Azure Databricks: batch ingestion with PySpark DataFrames, SQL-based file loading with **COPY INTO**, aggregated table creation with **CTAS**, and continuous file detection with **Auto Loader**.

By the end of this lab, you will be able to:

- Create a Unity Catalog hierarchy (catalog, schema, volume) to house ingested data
- Load CSV data from a managed volume into a Delta table using PySpark DataFrames
- Use COPY INTO to incrementally load files with built-in deduplication
- Create summary tables using CREATE TABLE AS SELECT
- Configure Auto Loader to automatically detect and process new files from cloud storage

---

## 🤖 Genie Code — use it throughout this lab!

You are expected and encouraged to use the **Genie Code** for all exercises. Genie Code is available directly in the notebook cell toolbar. Use it to:

- Look up syntax for SQL and PySpark operations
- Explain error messages
- Generate boilerplate code that you then adapt
- Ask follow-up questions about how things work

To open Genie Code, select the ![assistant-icon](https://raw.githubusercontent.com/MicrosoftLearning/DP-750T00-Implement-Data-Engineering-Solutions-using-Azure-Databricks/refs/heads/main/Allfiles/media/genie-code.svg) on the right side of any notebook cell, or use the keyboard shortcut.

💡 **Each exercise cell includes a suggested prompt you can copy directly into Genie Code to get started.**

---

## 🔑 Lab environment note: your personal catalog

In this lab environment, several students share one Unity Catalog metastore, and a catalog name can only exist once in a metastore. To keep your work separate, the lab notebook adds your personal **lab ID** (8 characters, for example `1a2b3c4d`) to the catalog name, so this lab's `solaris_lab` catalog is called **`solaris_lab_<lab ID>`** for you.

- The first code cell in the notebook prints your lab ID and catalog name. **Write them down** — your lab ID is the same in every lab.
- Wherever these instructions show `<lab ID>`, replace it with your own lab ID.
- If your notebook session restarts (for example after a break) and you see *SCHEMA_NOT_FOUND* or *TABLE_OR_VIEW_NOT_FOUND* errors, run the notebook's setup cell again.

---

## Prerequisites

- An **Azure Databricks Premium workspace** provisioned using [Lab 00: Set up your Azure Databricks environment](00-setup.md).
- You have the **Data Engineer** or equivalent role in the workspace, with permission to create catalogs and volumes
- Basic familiarity with SQL and Python

---

## Non-notebook exploration: Lakeflow Spark Declarative Pipelines (optional)

**Lakeflow Spark Declarative Pipelines** (formerly Delta Live Tables) is the recommended way to build production-grade ingestion pipelines with automatic orchestration, schema management, and exactly-once guarantees.

To explore the pipeline editor:

1. In the sidebar, select **Jobs & Pipelines**.
2. Select **Create** and then **ETL pipeline**.
3. Review the options for specifying a source notebook or SQL file, naming the pipeline catalog and schema, and choosing a cluster type.
4. Click **Cancel** — you do not need to create or run a pipeline.

---

## Importing the notebook

Follow these steps to import the lab notebook into your Databricks workspace:

1. In the Databricks workspace, click **Workspace** in the left sidebar.
2. Navigate to or create a folder where you want to store the lab (for example, /Users/<your-email>/Labs).
3. Click the **⋮** (kebab) menu or right-click the folder, then select **Import**.
4. Choose **URL**, enter the following URL, and click **Import**:
   `{{FILES_BASE_URL}}/Allfiles/07-ingest-data-into-unity-catalog.ipynb`
5. Open the imported notebook and, in the compute selector at the top, choose **Serverless** compute.

---

## Lab overview

The notebook is structured into four exercises:

| Exercise | Topic | Technique |
|---|---|---|
| 1 | Set up the catalog hierarchy | SQL DDL — CREATE CATALOG, CREATE SCHEMA, CREATE VOLUME |
| 2 | Batch ingestion with DataFrames | PySpark spark.read / df.write |
| 3 | SQL-based file ingestion | COPY INTO, CREATE TABLE AS SELECT |
| 4 | Auto Loader | cloudFiles format with spark.readStream |

Work through the exercises in order. Each exercise builds on the catalog and data created in the previous one.
