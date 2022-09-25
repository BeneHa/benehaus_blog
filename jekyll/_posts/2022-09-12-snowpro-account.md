---
title: Snowpro Core preparation part 3 -  Account and security
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


So, let's jump right into the third topic, which is account and security:

<h2>Account and security</h2>

Encryption:  
- Snowflake encrypts all data by default at no additional cost
- Only the customer or runtime components can read the data
- The customer puts encrypted data to the external staging area and provides Snowflake with the encryption master key
- For Snowflake stages, the customer provides unencrpyted data which Snowflake will encrypt automatically
- States of encryption keys: active, retired, destroyed

Security overall:  
- You can create multiple network policies of whitelists and blacklists of IP ranges but only have one active at the time (by the way, it is 2022, how about allow- and blocklists?)
- Authentication can be done using passwords, single sign on or multi-factor authentication
- Role based access control (RBAC) is used for all objects, no permissions are granted to users directly
- Discretionary access control: each object has an owner that can grant others permissions on that object
- Key hierarchy: Root key -> master key -> object master key -> file key
    - Keys are rotated every 30 days, annual re-keying is option for accounts above Enterprise level

Procedures:  
- Caller`s rights:
    - Runs with privileges of the caller
    - Use warehouse, database, schema that is currently used
    - Can view, set, unset the caller`s session variables and parameters
- Owner`s rights:
    - Default
    - Uses database and schema that the procedure is created in
    - Cannot access most caller-specific information
    - Cannot query INFORMATION_SCHEMA table functions that return results based on the current user
    - Does not allow non-owners to view information about the procedure in the PROCEDURES view