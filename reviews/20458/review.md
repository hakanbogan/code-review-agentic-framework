# Code Review

## Summary
Reviewed PR #20458: Fixed #36644 — Add deprecation warning for order_by() without arguments used with first()/last().
Changed 0 files (+0/-0)
Found 7 issues requiring attention.

## 🟠 Major Issues

### Missing docstring for public methods

**Location:** `django/db/models/query.py:1155, 1168`  
**Type:** other  
**Source:** documentation_analysis  

Public methods 'first()' and 'last()' in QuerySet class lack docstrings explaining their new behavior with deprecation warnings.

**Suggested fix:**
```
+++ b/django/db/models/query.py
@@ -1155,6 +1155,7 @@
 
     def first(self):
         """Return the first object of a query or None if no match is found.
+        Deprecated: Calling first() without explicit ordering will default to 'pk' ordering in Django 7.0.
         """
         if self.ordered:
             queryset = self
@@ -1168,6 +1169,7 @@
# ... patch truncated
```

### Missing test case documentation

**Location:** `tests/get_earliest_or_latest/tests.py:266`  
**Type:** other  
**Source:** documentation_analysis  

New test cases in 'tests/get_earliest_or_latest/tests.py' lack comments explaining the purpose and expected outcomes of the tests.

**Suggested fix:**
```
--- a/tests/get_earliest_or_latest/tests.py
+++ b/tests/get_earliest_or_latest/tests.py
@@ -265,6 +265,16 @@ class TestFirstLast(TestCase):
         with self.assertRaisesMessage(TypeError, msg % "last"):
             qs.last()
 
+    """
+    Test the deprecation warnings for calling first() and last() after order_by() with no arguments.
+    - Verifies that a deprecation warning is raised for both first() and last() when called after an empty order_by().
+    - Checks that no warning is raised when order_by() is called with explicit arguments.
# ... patch truncated
```

### Undocumented deprecation warning

**Location:** `N/A`  
**Type:** other  
**Source:** documentation_analysis  

The deprecation warning introduced for 'first()' and 'last()' methods when called without arguments after 'order_by()' is not documented in the API documentation.

**Suggested fix:**
```
diff --git a/docs/ref/models/querysets.txt b/docs/ref/models/querysets.txt
index 1234567..89abcde 100644
--- a/docs/ref/models/querysets.txt
+++ b/docs/ref/models/querysets.txt
@@ -xxxx,6 +xxxx,12 @@ The API reference for ``QuerySet``:
     .. method:: first()
     
        Returns the first object matched by the queryset, or ``None`` if there is no matching object. If the queryset has no ordering defined, it orders by the primary key.
+       
+       .. deprecated:: 3.2
# ... patch truncated
```

### Missing tests for deprecation warning logic

**Location:** `django/db/models/query.py`  
**Type:** other  
**Source:** test_analysis  

The changes introduce a deprecation warning for calling first()/last() after order_by() with no arguments. However, there are no tests ensuring that the warning is only triggered under the correct conditions (i.e., when default ordering is not set and no arguments are passed to order_by()).

**Suggested fix:**
```
diff --git a/tests/db/models/test_deprecation.py b/tests/db/models/test_deprecation.py
new file mode 100644
index 0000000000..1111111111
--- /dev/null
+++ b/tests/db/models/test_deprecation.py
@@ -0,0 +1,10 @@
+from django.db import models
+from django.test import TestCase
+from django.utils.deprecation import RemovedInDjango70Warning
+
# ... patch truncated
```


## 🟡 Minor Issues

### Outdated comment

**Location:** `django/db/models/query.py:1156, 1169`  
**Type:** other  
**Source:** documentation_analysis  

Comments within 'first()' and 'last()' methods refer to a future change as if it's pending, but do not clarify the current state adequately.

### Incomplete PR checklist

**Location:** `PR Description`  
**Type:** other  
**Source:** documentation_analysis  

The PR checklist mentions 'I have added or updated relevant docs, including release notes if applicable.' as unchecked, indicating potential missing documentation updates.

### Test file modified without assertions

**Location:** `tests/get_earliest_or_latest/tests.py`  
**Type:** other  
**Source:** static_analysis  

Test file changes don't include assertions. Tests should verify expected behavior.

