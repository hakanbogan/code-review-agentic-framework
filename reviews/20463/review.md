# Code Review

## Summary
Reviewed PR #20463: Fixed #36355 -- Included applied cross-app migrations in sqlmigrate state.
Changed 0 files (+0/-0)
Found 4 issues requiring attention.

## 🟠 Major Issues

### Potential for applying migrations out of order

**Location:** `django/db/migrations/loader.py:433-454`  
**Type:** logic  
**Source:** logic_analysis  

The logic in _create_project_state_for_collect_sql may lead to migrations being applied out of their intended order. This can happen because it iterates over all leaf nodes and applies pending migrations without considering the dependencies between different apps' migrations.

### Potential inefficient graph traversal

**Location:** `django/db/migrations/loader.py:431-461`  
**Type:** performance  
**Source:** performance_analysis  

The implementation of `_create_project_state_for_collect_sql` method may lead to inefficient graph traversal, especially for large dependency graphs.

**Suggested fix:**
```
+++ b/django/db/migrations/loader.py
@@ -431,7 +431,7 @@ class MigrationLoader:
         """
         Create a ProjectState for collect_sql that includes applied migrations
         from other apps not in the target migration's dependency graph.
-        """
+        Efficient traversal implementation needed here. """
         target_plan_set = set(self.graph.forwards_plan(node))
         state = self.project_state(node, at_end=at_end)
```


## 🟡 Minor Issues

### Missing documentation for new method

**Location:** `django/db/migrations/loader.py:422`  
**Type:** logic  
**Source:** logic_analysis  

The method _create_project_state_for_collect_sql lacks documentation on its purpose, usage, and the implications of including migrations from apps not in the target migration's dependency graph.

### Test file modified without assertions

**Location:** `tests/migrations/migrations_test_apps/cross_app_fk/app_a/migrations/0001_initial.py`  
**Type:** other  
**Source:** static_analysis  

Test file changes don't include assertions. Tests should verify expected behavior.

