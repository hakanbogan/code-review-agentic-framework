# Code Review

## Summary
Reviewed PR #20460: Fixed #36821 -- Treated empty strings as NULL for iexact lookups on Oracle.
Changed 0 files (+0/-0)
Found 3 issues requiring attention.

## 🟠 Major Issues

### Inconsistent behavior for non-Oracle databases

**Location:** `django/db/models/sql/query.py:1447`  
**Type:** logic  
**Source:** logic_analysis  

The change assumes all databases treat empty strings as NULLs, which may not be true for databases other than Oracle. This could lead to inconsistent behavior across different database backends.

**Suggested fix:**
```
--- a/django/db/models/sql/query.py
+++ b/django/db/models/sql/query.py
@@ -1444,7 +1444,8 @@ class Query(BaseExpression):
         if (
             lookup_name in ("exact", "iexact")
             and lookup.rhs == ""
-            and connections[DEFAULT_DB_ALIAS].features.interprets_empty_strings_as_nulls
+            and connections[lookup.lhs.alias].features.interprets_empty_strings_as_nulls
         ):
```

### Test coverage for 'iexact' lookup change

**Location:** `django/db/models/sql/query.py:1444`  
**Type:** other  
**Source:** test_analysis  

The modification to treat empty strings as NULL for iexact lookups on Oracle is significant and requires comprehensive test coverage. The provided test case covers the basic scenario where an empty string is treated as NULL, but additional edge cases and scenarios should be tested to ensure robustness.


## 🟡 Minor Issues

### Test file modified without assertions

**Location:** `tests/queries/tests.py`  
**Type:** other  
**Source:** static_analysis  

Test file changes don't include assertions. Tests should verify expected behavior.

