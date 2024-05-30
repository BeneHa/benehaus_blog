---
title: Snowpro Core preparation part 5 - Overview and architecture
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


So, let's jump right into the fifth topic, which is overview and architecture:

<h2>Overview</h2>

- Snowflake is a multi-cluster, shared data OLAP service
- Services layer: optimization, management, security, metadata
- Multi cluster compute: compute warehouses
- Centralized storage: data storage
- Cloud agnostic layer: allows to run on AWS, GCP and Azure
- Deployed within virtual private network

Snowflake versions:
- Standard: 1 day time travel, business hour support
- Enterprise: multi-cluster warehouse, 90 days time travel, materialized views, annual rekeying of data
- Business Critical: HIPPA/PCI compliance, data encryption everywhere, tri-secret secure, database failover and fallback for business continuity
- Virtual Private Snowflake: customer dedicated virtual servers and metadata store

Snowflake objects:
- Organization (announced)
- User, role, warehouse, resource monitor
- Database > Schema > table, view, stored procedure, UDF, stage, file format, pipe, sequence

Table types:
- Permanent: up to 90 days time travel, fail-safe, persist until dropped
- Temporary: 0 or 1 day time travel, no fail-safe, tied to single session
- Transient: 0 or 1 day time travel, no fail-safe, persist until dropped
    - There are also transient databases and schemas
- External: Snowflake table over an external data lake, read-only, no time travel or fail-safe

View types:
- Standard: default, named definition of a query, executes as owning role
- Secure: Definition and details only visible to authorized users, optimizer bypasses some optimizations used for regular views
- Materialized: stores results of underlying query, auto-refresh, no warehouse needed
    - Secure materialized view also supported

Cloud services layer:
- Brains of the service
- Management: centralized management for all storage
- Optimizer: cost-based SQL optimizer with automatic JOIN order optimization
- Security: authentication, access control, encryption, key management
- Metadata management: stores metadata, handles metadata queries
