---
title: Nondeterministic behaviour of Snowflake based on warehouses
image: assets/images/blogposts/2022-08-14-snowflake-nondeterministic/snowflake.png
categories: [ Technical, Snowflake ]
---

In the past week I stumbled upon a weird behaviour in Snowflake when a colleague asked me to help with a problem he did not understand. Basically, a data load process behaved differently if it was run from different tools (manually calling the Stored Procedure or calling it from Azure Data Factory). We narrowed it down to a view which does some business logic and should, given the same input data, always output the same result.  

Now there are some cases when views do not output the same when called several times. The most obvious case would be a call to a random number generating function. Also a row-level access policy set on a table used in the view can yield different results if the view is called with different users.  

At first we found no likely suspect for such a function in the view. With some more testing we discovered one more weird fact: The output of the view was actually deterministic and reproducible, but it varied based on which warehouse was used for the calculation. This is strange as usually a Snowflake warehouse just represents some blackbox compute power in the cloud you do not need to worry about, it does not have any influence on the content of your data, just on how fast it will be calculated.  

Upon some more looking around at the view code we finally found the issue: the view contained a SEQ4() function for ordering data within groups and then filtering based on this order. This is what makes it non-deterministic as is clearly written in the <a href="https://docs.snowflake.com/en/sql-reference/functions/seq1.html">documentation</a> that is really helpful here if you read it:

```
This function uses sequences to produce a unique set of increasing integers,  
  but does not necessarily produce a gap-free sequence.  
 When operating on a large quantity of data, gaps can appear in a sequence.  
 If a fully ordered, gap-free sequence is required,  
  consider using the ROW_NUMBER window function.
```

This explains why the view did not yield the same result. It is still interesting to see that the view did indeed yield the same result when using the same warehouse for the calculations (we tested this several times and it was reproducible). It seems that for generating this sequence some kind of seed is being used that is unique to the warehouse. This part is unclear to me as there is no way to look behind the scenes of how Snowflake calculates things, but for the problem at hand the solution was easy, just as described in the documentation: using the ROW_NUMBER function worked in this case.  

For me this was an interesting discovery as it is one of those edge cases you do not know to exist before you see them. And it reminded me that especially for highly managed cloud services like Snowflake that hide a great deal of complexity from the user, you need to think about what you are doing read the documentation and think about where you are trusting the managed solution to handle things properly for you because you might just miss one detail that will screw up your entire load process.