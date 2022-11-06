---
title: Snowpro Data Engineer part 3 - Storage & Data protections
image: assets/images/blogposts/2022-09-27-snowpro-engineer/snowpro-engineer.png
categories: [ Technical, Snowflake ]
---

Time travel:
- Time travel up to 90 days, then Fail-Safe 7 days for permanent tables
- Standard retention: 24 hours
- Changing retention on schema changes it for all objects in that schema that do not have a retention period explicitly set
- Dropping a schema does not honor the explicitly set retention period of child objects but overwrites it with the schema's value

Parameters hierarchy:
    - Account session parameter overwritten by user session parameter (set by admin or user) overwritten by user
    - Account object parameter overwritten by warehouse parameter
    - Account object parameter overwritten by database object parameter overwritten by schema object parameter overwritten by table, pipe etc. object parameter

Parameter examples:
- MAX_RECURSIONS limits number of iterations

Database replication:
- Both accounts need to be business critical or higher
- Not replicated: temporary tables, external tables, stages, temporary stages, pipes
- Privileges are not replicated
- Billing: data transfer (initial and subsequent), compute
- Replication can be to different account in same organization

Clustering:
- SYTEM$CLUSTERING_INFORMMATION for information live average depth for a table
- SYTEM$CLUSTERING_DEPTH for average depth of table; always 1 or more
    - The smaller the depth, the better clustered the table is