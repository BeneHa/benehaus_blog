---
title: Snowpro Core preparation part 2 -  storage and protection
image: assets/images/blogposts/2022-08-27-snowpro-warehouses/snowpro-certification-core.png
categories: [ Technical, Snowflake ]
---
I am currently preparing for the SnowPro Core certification which is the standard technical Snowflake certifications. More specialized certifications can be gained after this one is achieved. More details can be found on the <a href="https://www.snowflake.com/certifications/">Snowflake website</a>.  

Other articles in this series:  
<a href="../snowpro-warehouses">Part 1 - Warehouses</a>   
<a href="../snowpro-storage">Part 2 - Storage</a>  
<a href="../snowpro-account">Part 3 - Account and security</a>   
<a href="../snowpro-movement">Part 4 - Data movement</a>  
<a href="../snowpro-overview">Part 5 - Overview and architecture</a>
<a href="../snowpro-performance">Part 6 - Performance tuning</a>
<a href="../snowpro-semistructured">Part 7 - Semi-structured data</a>



So, let's jump right into the second topic, which is storage and protection:

<h2>Storage</h2>

- Automatic micro-partitioning of table data​
- Partitioned based on ingestion order, can be changed by defining a clustering key​
- Each micro partition is optimally compressed based on the data type​
- Per micro partition: max 16 MB compressed, 50-500 MB uncompressed​
- Immutable  --> update writes new version; services layer knows which version of a tables consists of which versions of the partitions  --> time travel!​
- Partition metadata is used for optimizing queries by not scanning certain partitions if there are filtering predicates

<h2>Data Protection:</h2>

- All communication and all data at rest encrypted end-to-end​
- Each micro partition has its own encryption key​
- All data replicated across availability zones

<h2>Clustering:</h2>

Benefits:​
- Improve scan efficiency in queries by skipping data that does not match the filter predicates (just certain micro partitions are read).​
- Better compression per column​
- After a key is defined the only modification to administer is drop or modify the key​
  
Considerations:​
- Use on tables with a large number of micro partitions (Typically multiple terabytes).​
- Query advantages (one or both):​
    - The queries are selective (only read the necessary micro partitions).​
    - The queries sort the data (ORDER BY clause)​
- High number of queries can benefit if they use the same few columns (or at least the key columns)

Table and view types are well described in these images from Snowflake:

{% include image.html
    url="/assets/images/blogposts/2022-09-05-snowpro-storage/table_types.png"
    description="The different types of tables in Snowflake"
    alt="Snowflake table types" %}

{% include image.html
    url="/assets/images/blogposts/2022-09-05-snowpro-storage/view_types.png"
    description="The different types of views in Snowflake"
    alt="Snowflake view types" %}