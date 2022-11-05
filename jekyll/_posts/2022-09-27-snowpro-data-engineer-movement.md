---
title: Snowpro Data Engineer part 1 - Data Movement
image: assets/images/blogposts/2022-09-27-snowpro-engineer/snowpro-engineer.png
categories: [ Technical, Snowflake ]
---

After recently having completed my SnowPro Core exam, I am now preparing to take the Snowpro Data Engineer Exam. There is less preparation material, mainly no video series but mainly a study guide which describes the relevant topics but mainly collects links to the Snowflake documentation. So I will try to take notes for the exam using this blog. Let's see how it goes.

External Functions:
- referred to in SQL statement
- calls an external API
- Setup: create API integration, then external function based on it

Spark integration:
- Spark driver sends SQL query using JDBC, Snowflake uses warehouse to process query and copies result to S3, connector retrieves data from S3 and puts it in Spark data frame
    - Snowflake handles processing for egress, Spark worker nodes handle data ingress
- Query pushdown can handle complex Spark logical plans
- Data is located in Snowflake, so process most things there instead of transferring large intermediate results
- Catalyst produces optimized logical plan, then Spark decides whether to push down query to Snowflake

- Apache Arrow can be used for optimized query result fetching from Snowflake

ETL vs. ELT:
- ETL works well for relational data that must maintain tabular structure
- ETL for small data volume, source and target require different data types, primarily structured data
- ELT is better for semi-structured data that must be maintained in its form until use cases are clear
- ELT for large data volume, source and target database of same type, data is semi- or unstructured

Continuous data loading:
- Use Snowpipe, Snowflake Connector for Kafka, third-party data integration tools
- Change data tracking: use streams
- Recurring tasks: use tasks, e.g. by chaining and reading from a stream

Connectors and drivers:
- Snowflake connector for Python
- Snowflake connector for Spark
- Snowflake connector for Kafka
- Node.js driver
- Go driver
- .NET driver
- JDBC driver
- ODBC driver
- PHP PDO driver
- Snowflake SQL API

Data sharing:
- Secure Direct Data Sharing: create share, add objects by granting privileges, add accounts to share
- Snowflake Marketplace: all non-VPS accounts, become provider or consumer, IMPORT SHARE necessary to get or request data
- Data Exchange: own data hab for collaborating around data between selected group of members

COPY INTO:
- loads from named internal stage (table / user stage), load files there using PUT, or named external stage
- Validation_mode: RETURN_n_ROWS, RETURN_ERRORS, RETURN_ALL_ERRORS
- FORMAT_NAME and TYPE are mutually exclusive
- Compression: gzip, bz2, brotli, zstd, deflate, raw_deflate
- Allowed operations: column reordering, omission, casts, truncating text strings that exceed column length

Data movement:
- per-byte fee when transferring from Snowflake account into cloud storages in another region or another cloud platform
- Egress charges: for unloading from Snowflake, database replication, external functions

Misc commands:
- DESCRIBE STAGE: describes values specified for properties in a stage (file format, copy, location) as well as defaults
- CREATE FILE FORMAT: file format describes set of staged data to be loaded into Snowflake
- VALIDATE_PIPE_LOAD: validate files processed by Snowpipe within time range (up to last 14 days)
- COPY_HISTORY table function: Snowflake data loading history, returns files loaded using COPY INTO and Snowpipe
    - more than the 10.000 rows in the LOAD_HISTORY view
- CREATE STREAM: new stream recording changes for a source object
- CREATE TASK: new task, can be cloned, schedule is optional
- CREATE EXTERNAL TABLE:
    - no clustering keys, cloning, xml data, time travel, masking policy
    - METADATA$FILENAME, METADATA$FILE_ROW_NUMBER for file information
    - row access policy can be added
    - use POLICY_CONTEXT for simulating query results

Misc queries:
- PIPE_LOAD_STATUS for validating loads