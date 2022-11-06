---
title: Snowpro Core preparation part 1 -  virtual warehouses
image: assets/images/blogposts/2022-08-27-snowpro-warehouses/snowpro-certification-core.png
categories: [ Technical, Snowflake ]
---
I am currently preparing for the SnowPro Core certification which is the standard technical Snowflake certifications. More specialized certifications can be gained after this one is achieved. More details can be found on the <a href="https://www.snowflake.com/certifications/">Snowflake website</a>.  
For each of the topics I will be collecting information for the test in the form of bullet points which I will share here. This is not a full list of everything that will help you pass this exam, but simply my personal study notes. If the help you preparing, great, but please do not use them as the sole source for studying!  

The study guide can be found [here](../assets/documents/snowflake/COF-CO2_SnowProCoreStudyGuide_090922.pdf).

The whole series:  
<a href="../snowpro-warehouses">Part 1 - Warehouses</a>   
<a href="../snowpro-storage">Part 2 - Storage</a>  
<a href="../snowpro-account">Part 3 - Account and security</a>   
<a href="../snowpro-movement">Part 4 - Data movement</a>  
<a href="../snowpro-overview">Part 5 - Overview and architecture</a>
<a href="../snowpro-performance">Part 6 - Performance tuning</a>
<a href="../snowpro-semistructured">Part 7 - Semi-structured data</a>

So, let's jump right into the first topic, which for me was the virtual warehouses:

- Warehouse size determines number of servers in each cluster​
- Default: XL (GUI), XS (SQL)​
- Economy: waits 6 minutes before scaling out, Standard scales out immediately​
- Auto suspend: lowest 5 minutes in GUI, 1 minute in SQL according to video but it is actually possible if you try it
- Warehouse is needed if underlying data for a query changed, otherwise result cache is used​
- No warehouse needed for queries on metadata cache (count, min, max, num distinct values)​
- Result cache is used if same query is used by same role within 24 hours and no data changed (why the same role is needed is not clear to me from an implementation standpoint)​
- Compute at cloud services layer: charged if exceeds 10% of total compute costs for account -> WAREHOUSE_METERING_HISTORY view​
- Resizing warehouses does not interrupt queries​
- Scale up: solves complex query problem, scale out: solves concurrency problem