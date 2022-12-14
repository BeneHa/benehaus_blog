---
title: Snowpro Data Engineer part 4 - Data transformations
image: assets/images/blogposts/2022-09-27-snowpro-engineer/snowpro-engineer.png
categories: [ Technical, Snowflake ]
---

Arrays:
- Parse using FROM tab, table(flatten(tab.column))
- Use lateral views where each view is based on the previous level for multiple levels of objects