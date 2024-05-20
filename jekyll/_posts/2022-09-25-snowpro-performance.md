---
title: Snowpro Core preparation part 6 - performance tuning
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


So, let's jump right into the sixth topic, which is performance tuning:

- Query optimization first looks at row filtering (from, join, where), then groups (group by, having), then the result (distinct, order limit)
- Use filters as early as possible
- Query out of memory -> spill to disk is always slower than in memory
- Subqueries:
    - Uncorrelated: subquery has no information depending on outer query
    - Correlated: dependency of subquery to main query, so subquery changes for every row in table, takes much longer as a result
- Group by column with few distinct values

Data clustering:
- By default tables will be sorted into micro partitions depending on ingest order
- Use one to three clustering keys maximum, key can be expression (e.g. TO_DATE(col_name))
- Clustering is billed per second, frequently changing tables can be expensive to cluster

Warehouse scaling:
- Scale up for complex queries, scale out for parallel queries
- Economy scaling waits for 6 minutes before it scales out to a new cluster
