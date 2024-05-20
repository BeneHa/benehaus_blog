--
title: "Postgres reading notes"
image:
categories: [ Databases ]
---

# Intro

I am currently reading the book [Mastering PostgreSQL 15](https://www.amazon.de/Mastering-PostgreSQL-techniques-fault-tolerant-applications/dp/1803248343/ref=sr_1_1?__mk_de_DE=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=1Y8H2UUXJYZOY&keywords=mastering+postgres+15&qid=1694781954&sprefix=mastering+postgresql+15%2Caps%2C88&sr=8-1) in order to get a better understanding of this specific database technology. In the past I was working more with analytical/OLAP-oriented databases like Snowflake, but now OLTP databases are more important to my current job, so I decided to start getting into that with Postgres. I will share my reading notes here.

# Transactions and Locking

- transaction chaining using COMMIT AND CHAIN
- savepoints using SAVEPOINT abc
- most DDL statements are transactional!
- Multi-Versions Concurrency Control: a transaction can see data that has been committed before the start of this transaction
    - Writes do not block reads
    - In Concurrent write transactions, the second write will wait until the first one has committed
- SELECT ... FOR UPDATE lets you select rows and update these rows in a later statement, avoiding race conditions when two processes do a select and update just with WHERE conditions - nice!
    - NOWAIT or lock_timeout to avoid waiting for the other process to long
    - SKIP LOCKED will let a second transaction do a select, skipping the locked rows from the first transaction
- Supported isolation levels: read committed, repeatable read, serializable
- Unique row identifier: ctid, can be used as SELECT ctid ... or WHERE ctid ...
- Advisory locks: named locks, SELECT pg_advisory_lock(1) waits until lock named "1" is released
- VACUUM cleans up unused space in the file system, tables will remain the same size
    - autovacuum usually runs every minute, no manual start needed
    - VACUUM FULL rebuilds a table but locks it completely, avoid usint it!
    - If there is free space in a table after a VACUUM, it will be used by the next command allocating memory for this table
    - Row gets delted if it cannot be seen any more by anybody

# Indexes

- Index in postgres is a B-tree
- EXPLAIN to show details of execution plan
- Execution costs are calculated with points: reading one sequential block costs one point (configured by seq_page_cost)
    - cpu_tuple_cost and cpu_operator_cost needed for processing the blocks; many more cost parameters e.g. for parallel queries
    - Costs are an estimate, cannot be translated to real execution time
- One index can be used in a single query multiple times (e.g. search for a column equal to one value OR another value)
- Query optimizer can decide not use an index if it does not make sense based on the table statistics
    - Plans change based on the queries input values because postgres will optimize based on those
- CLUSTER tables in order to store them in the same order as an index
    - Locks the table while running
    - Table can only be clustered by one indes
    - Clustered state of table will not be maintained automatically!
- Index-only scan: If just the index column is queried, it is not necessary to go to the actual table storage
