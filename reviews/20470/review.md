# Code Review

## Summary
Reviewed PR #20470: Fixed #36391 -- Doc'd RawSQL usage on “Performing raw SQL queries” page.
Changed 0 files (+0/-0)
Found 1 issues requiring attention.

## 🟡 Minor Issues

### Documentation update lacks corresponding test cases

**Location:** `docs/topics/db/sql.txt`  
**Type:** other  
**Source:** test_analysis  

The documentation for 'Performing raw SQL queries' has been updated to include new information about using RawSQL for embedding raw SQL fragments into ORM queries. However, there are no corresponding updates to test cases that verify the new examples and guidelines work as expected and are clear to the end users.

