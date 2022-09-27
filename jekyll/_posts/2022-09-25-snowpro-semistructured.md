---
title: Snowpro Core preparation part 7 - semi-structured data
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

So, let's jump right into the seventh topic, which is semi-structured data:

- Snowflake supports JSON, AVRO, ORC, Parquet, XML
- Types:
    - Variant: standard SQL types, array, objects
    - Object: key-value pairs, value is VARIANT
    - Array: value is VARIANT
- Access value with k:v or k['v'] syntax
- Cast with double colon (::) syntax
- Flatten, lateral join often used for flattening a json

Loading and unloading:  
- Very similar to structured data
- Create file format, use it in COPY INTO
- Unloading supports JSON and parquet
