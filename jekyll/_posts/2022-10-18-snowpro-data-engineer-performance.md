---
title: Snowpro Data Engineer part 2 - Performance optimization
image: assets/images/blogposts/2022-09-27-snowpro-engineer/snowpro-engineer.png
categories: [ Technical, Snowflake ]
---

Local and remote spilling
- When query does not fit into memory, spilling first goes to local disc of warehouse node, then to remote storage

Queries:
- Unnecessary joins can be removed by Snowflake if a constraint (e.g. PRIMARY KEY) is set with the RELY property
- Correlated subquery refers to columns outside of query, uncorrelated does not
- Scalar subquery returns a single value
- Predicate with subquery cannot be used for pruning even if it returns a constant

Hierarchical data:
- Join table on itself to query many levels in e.g. manager - employee relation
- Recursive CTE: WITH clause that refers to itself
- CONNECT BY: processes hierarchy one at a time, each level refers to prior level
    - Cannot add new columns

Recognize matching rows:
- Use MATCH_RECOGNIZE: first define partition by and order by, then the pattern by using pattern variables defined with DEFINE, then define what to return (e.g. ONE ROW PER MATCH)

Persisted results:
- Query result persisted for 24 hours, security token for large persisted query results expires after 6 hours
- Conditions for re-using cached result: same syntax, no functions evaluated at execution time, no UDF / external functions, no change in table data, result is still available, role has required privileges, no change in micro partitions; still no guarantee that results are reused
- For further processing use RESULT_SCAN

Distinct values:
- Speed up using APPROX_COUNT_DISTINCT
- Use Bitmaps for hierarchical aggregations and dense values: BITMAP_BUCKET_NUMBER, BITMAP_CONSTRUCT_AGG(BITMAP_BIT_POSITION(val))
- Use arrays for hierarchical aggregations: ARRAY_UNIQUE_AGG

Similarity:
- Calculate MINHASH and compare using APPROXIMATE_SIMILARITY / APPROXIMATE_JACCARD_INDEX

Frequent values:
- Estimate using APPROX_TOP_K or APPROX_TOP_K_COMBINE: percentage of error depends on data skew

System functions:
- Control functions for actions in the system
- Information functions about the system
- Information functions about queries

Account usage:
- Information schema: no dropped objects, no latency, 7 days to 6 month retention
- Account usage: dropped objects, 45 minutes to 3 hours latency, 1 year retention

Query history:
- Query by time range, session, user, warehouse
- Only query with time range returns all queries, otherwise last 100 queries

Search optimization service:
- Improves point lookups, substring and regex searches, queries on VARIANT / OBJECT / ARRAY, queries with GEOGRAPHY values
- Maintenance service creates optimized search access path
- ESTIMATE_SEARCH_OPTIMIZATION_COSTS returns build costs, storage costs, compute costs
- Create using ALTER TABLE tab ADD SEARCH OPTIMIZATION

Storage:
- Use TABLE_STORAGE_METRICS view
- High churn tables: create as transient, copy to permanent table regularly (which then has the time travel information)

Query acceleration:
- Benefitial for ad hoc analytics, workloads with unpredictable data volume per query, large scans and selective filters
- Use view SYSTEM%ESTIMATE_QUERY_ACCELERATION
- Billed as a serverless feature per second

COPY_HISTORY
- data loading history for 14 days (LOAD_HISTORY: 365 days)
- more then 10.000 rows which is the limit for LOAD_HISTORY
- includes Snowpipe data (LOAD_HISTORY: not)

Other functions:
- TASK_HISTORY for tasks within las 7 or next 8 days
- SHOW STREAMS to list streams
- PIPE_USAGE_HISTORY for Snowpipe history of last 365 days, up to 3 hours latency
