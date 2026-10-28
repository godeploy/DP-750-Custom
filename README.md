# DP-750 labs: GoDeploy shared-environment edition

These are edited copies of the official Microsoft DP-750 lab notebooks and guides
(source: `MicrosoftLearning/DP-750T00-Implement-Data-Engineering-Solutions-using-Azure-Databricks`,
`main` branch, commit `132c097`). The official repository was not changed.

## The problem these edits fix

Every lab creates a catalog with a fixed name (`banking_lab`, `edu_dev`, `solaris_lab`, ...).
In the GoDeploy environment several students share one Unity Catalog metastore, and a catalog
name can only exist once per metastore. The first student creates `banking_lab` and owns it;
everyone after that gets `User does not have BROWSE on Catalog 'banking_lab'`.

## What changed

**Personal catalog names (labs 03–11 and 13).** Each notebook's first code cell now works out a
personal **lab ID**: 8 characters calculated from the student's user name and their workspace.
Every catalog gets it as a suffix, for example `banking_lab_1a2b3c4d`.

- The lab ID is the same in every lab for the same student and workspace.
- A new workspace gives a new lab ID, so catalogs left over from an old lab session never get in the way.
- The setup cell runs `USE CATALOG` on the student's catalog. Short names such as `silver.dim_customer`
  then point to the student's own catalog, so the exercises read almost the same as before.
- Where a full name or path is needed (volume paths, `ALTER CATALOG`, the SQL editor, job settings),
  the notebooks use the Python variable `catalog`, or tell students to type the name printed by the setup cell.
- Each notebook starts with a short "your personal lab ID" note, and each guide has a matching
  "Lab environment note".
- Cleanup cells now drop only the student's own catalog.

**Other shared names.**
- Lab 04: the group is now `retail-analysts-<lab ID>`, because account-level group names are shared
  too. The guide now creates the group after the first notebook cell has printed the name. The
  suggested Key Vault name is `kv-nm-<lab ID>`, which is globally unique.

**Fixes that were blocking students regardless of sharing.**
- Lab 09 pipeline file: removed a duplicated `@dp.table(name='gold.claims_summary')` decorator.
- Lab 09: the guide and starter code now use `try_cast` instead of `col().cast()`. With ANSI SQL
  mode, which serverless uses, a plain cast of `not-a-date` fails the whole pipeline. The official
  answer key already used `try_cast`.
- Lab 09 pipeline: reads the student's catalog from a pipeline configuration value, `lab_catalog`.
  The guide explains how to add it.
- Lab 04: the Task 1.2 TODO cell was mislabelled "Verify" and now says "Grant".
- Lab 05: the guide pointed at a `service_records` table that the lab never creates. The step now
  uses `vehicle_telemetry`.
- Default-catalog lookups now wrap the name in backticks, so a hyphenated workspace catalog name
  such as `adb-dp750` doesn't break the setup cell.

**Unchanged.** Labs 01, 02 and 12 notebooks, and the data files. Lab 01's guide only gets a note
that the workspace catalog may not be called exactly `adb-dp750`.

## Before you publish

1. Host the `Allfiles` folder somewhere students can reach (for example a GoDeploy-owned GitHub repo).
2. Run `python set_files_url.py <base URL>`. This replaces `{{FILES_BASE_URL}}` in the guides with
   the address of your hosted copy.
3. Run one lab end to end in a real GoDeploy environment. Lab 06 or 09 is a good choice, and ideally
   two students at once. These edits were checked for valid notebook format and Python syntax, and
   the setup cells were tested against a simulated Spark session, but not in a live Databricks workspace.

## Not fixed here (worth checking separately)

- **Lab 05, exercises 4–5** query `system.access.table_lineage` and `system.access.audit`. Students
  need `SELECT` on those system tables, which only an account or metastore admin can grant.
- **Lab 10**: the If/else task reads `{{tasks.check_quality.values.invalid_count}}`, but no notebook
  sets that value. If students run the job after adding it, that condition will most likely fail.
- **Lab 12**: the guide mentions an "Exercise 3" integration test that isn't in the notebook. This
  is cosmetic only.
- **Labs 00 / 99**: the setup and cleanup scripts create and delete a resource group. That needs
  subscription-level rights, so they don't apply when GoDeploy pre-deploys the workspace.
