---
title: Snowpro Core preparation part 4 - Data movement
image: assets/images/blogposts/2022-08-27-snowpro-warehouses/snowpro-certification-core.png
categories: [ Technical, Snowflake ]
---
I am currently preparing for the SnowPro Core certification which is the standard technical Snowflake certifications. More specialized certifications can be gained after this one is achieved. More details can be found on the <a href="https://www.snowflake.com/certifications/">Snowflake website</a>.

The whole series:
<a href="../snowpro-warehouses">Part 1 - Warehouses</a>
<a href="../snowpro-storage">Part 2 - Storage</a>
<a href="../snowpro-account">Part 3 - Account and security</a>
<a href="../snowpro-movement">Part 4 - Data movement</a>
<a href="../snowpro-overview">Part 5 - Overview and architecture</a>
<a href="../snowpro-performance">Part 6 - Performance tuning</a>
<a href="../snowpro-semistructured">Part 7 - Semi-structured data</a>


So, let's jump right into the fourth topic, which is data movement:

<h2>Data movement</h2>

Copy into command:
- COPY INTO is used for bulk and snowpipe data loads, as snowpipe so far only processed micro batches of data
- Snowpipe does not use a warehouse but Snowflake serverless compute (charged per core per second and scaled automatically)
- File formats and options can be set at
    - the COPY INTO command
    - the stage definition
    - the table definition
- For file formats options on level 1 override options on level 1 or 2 and are not cumulative
- Copy options on level 1 override options in lower levels but are cumulative

Semi-structured data:
- Try to extract elements containing NULL values to a separate column or use STRIP_NULL_VALUES = TRUE
- Ensure each unique element stores values of a single native data type
- This will help Snowflake store the objects in a columnar way instead of as objects which will make querying faster

Streams:
- A stream provides change data capture on tables, views and materialized views
- Contains new or updated values of the base object until the stream is consumed
    - If there are multiple consumers, you need to create multiple streams
- Two modes: standard and append-only
- Check if new data is available using SYSTEM$STREAM_HAS_DATA

Data unloading:
- The bigger the warehouse, the higher the possible parallelism, the more small files if SINGLE or MAX_FILE_SIZE are not set
- Use LIST and REMOVE commands to manage files in external stages
- You can use any SQL command during unloading
