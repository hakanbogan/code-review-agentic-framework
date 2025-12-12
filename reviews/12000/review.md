# Code Review

## Summary
Reviewed PR #12000: system to chart queries
Changed 0 files (+0/-0)
Found 192 issues requiring attention.

## 🔴 Critical Issues

### PR title does not match changes

**Location:** `mindsdb/__main__.py:341-343, mindsdb/api/a2a/agent.py:108-138`  
**Type:** consistency  
**Source:** change_analysis  

The PR title 'system to chart queries' suggests a feature addition or enhancement related to charting queries, but the actual changes involve removing a tokenizer feature and adjusting API response handling, which are unrelated to the PR title.

**Suggested fix:**
```
--- a/PR_Title.txt
+++ b/PR_Title.txt
@@ -1 +1 @@
-system to chart queries
+Remove tokenizer feature and adjust API response handling
```


## 🟠 Major Issues

### Removal of langchain handler without updating dependent features

**Location:** `default_handlers.txt:4`  
**Type:** logic  
**Source:** logic_analysis  

The removal of the langchain handler from default_handlers.txt could cause runtime errors or functionality loss for features depending on langchain.

**Suggested fix:**
```
--- a/default_handlers.txt
+++ b/default_handlers.txt
@@ -3,3 +3,4 @@
 postgres
 mysql
 openai
+langchain            # For agents & completions
```

### Removal of tokenizer loading without removing related configuration options

**Location:** `mindsdb/__main__.py:341-347`  
**Type:** logic  
**Source:** logic_analysis  

The code for loading the tokenizer has been removed, but there's no indication that related configuration options or documentation have been updated to reflect this change.

**Suggested fix:**
```
--- a/mindsdb/__main__.py
+++ b/mindsdb/__main__.py
@@ -341,21 +341,14 @@
         print(f"MindsDB {mindsdb_version}")
         sys.exit(0)
 
-    if config.cmd_args.update_gui or config.cmd_args.load_tokenizer:
+    if config.cmd_args.update_gui:
         if config.cmd_args.update_gui:
             from mindsdb.api.http.initialize import initialize_static
# ... patch truncated
```

### Incomplete transformation logic for chunk types

**Location:** `mindsdb/api/a2a/agent.py:108-138`  
**Type:** logic  
**Source:** logic_analysis  

The transformation logic for chunks in MindsDBAgent does not handle all possible types explicitly, potentially leading to incorrect behavior for unhandled types.

### Removal of skill-related functionality without removing all references

**Location:** `mindsdb/api/executor/command_executor.py`  
**Type:** logic  
**Source:** logic_analysis  

Skill-related functions are removed, but the codebase might still have references or dependencies on these functionalities, leading to potential runtime errors.

### Removal of tokenizer loading may impact feature functionality

**Location:** `mindsdb/__main__.py:341-357`  
**Type:** performance  
**Source:** performance_analysis  

The removal of the tokenizer loading feature from the startup sequence could potentially degrade the performance or functionality of features relying on natural language processing.

### Missing docstring for public class MindsDBAgent

**Location:** `mindsdb/api/a2a/agent.py:108`  
**Type:** other  
**Source:** documentation_analysis  

The class MindsDBAgent lacks a docstring explaining its purpose, parameters, and usage.

### Outdated docstring after code change

**Location:** `mindsdb/__main__.py:341`  
**Type:** other  
**Source:** documentation_analysis  

The removal of tokenizer loading functionality in __main__.py is not reflected in the module's docstring.

### Missing tests for new A2A format transformation logic

**Location:** `mindsdb/api/a2a/agent.py:108-145`  
**Type:** other  
**Source:** test_analysis  

The transformation logic in MindsDBAgent for converting HTTP endpoint format to A2A format lacks corresponding unit tests. This is critical as it affects data integrity and format consistency.


## 🟡 Minor Issues

### Inconsistent code commenting

**Location:** `mindsdb/__main__.py:343`  
**Type:** consistency  
**Source:** change_analysis  

The comment 'Tokenizer loading removed - was optional feature using langchain' in __main__.py does not follow the project's convention for documenting removed features, which typically includes a reason and a reference to an issue or decision.

### generic.secrets.security.detected-private-key.detected-private-key

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/docker/db_images/postgres/certs/server.key:1-2`  
**Type:** security  
**Source:** semgrep  



### yaml.docker-compose.security.no-new-privileges.no-new-privileges

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/docker/docker-compose-testing.yml:7-7`  
**Type:** security  
**Source:** semgrep  



### yaml.docker-compose.security.no-new-privileges.no-new-privileges

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/docker/docker-compose-testing.yml:15-15`  
**Type:** security  
**Source:** semgrep  



### yaml.docker-compose.security.no-new-privileges.no-new-privileges

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/docker/docker-compose-testing.yml:23-23`  
**Type:** security  
**Source:** semgrep  



### yaml.docker-compose.security.no-new-privileges.no-new-privileges

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/docker/docker-compose-testing.yml:32-32`  
**Type:** security  
**Source:** semgrep  



### python.fastapi.security.wildcard-cors.wildcard-cors

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/api/a2a/common/server/server.py:54-54`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/api/executor/utilities/sql.py:84-84`  
**Type:** security  
**Source:** semgrep  



### python.flask.security.audit.xss.make-response-with-unknown-content.make-response-with-unknown-content

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/api/http/initialize.py:432-432`  
**Type:** security  
**Source:** semgrep  



### python.django.security.injection.tainted-url-host.tainted-url-host

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/api/http/namespaces/auth.py:75-75`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.dangerous-globals-use.dangerous-globals-use

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/airtable_handler/airtable_handler.py:205-205`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.dangerous-globals-use.dangerous-globals-use

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/airtable_handler/airtable_handler.py:206-206`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/autogluon_handler/autogluon_handler.py:38-38`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/autogluon_handler/autogluon_handler.py:42-42`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/autosklearn_handler/autosklearn_handler.py:41-41`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/autosklearn_handler/autosklearn_handler.py:45-45`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/azure_blob_handler/azure_blob_handler.py:152-152`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/azure_blob_handler/azure_blob_handler.py:165-165`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/azure_blob_handler/azure_blob_handler.py:200-200`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/azure_blob_handler/azure_blob_handler.py:206-206`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-pickle

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/byom_handler/byom_handler.py:399-399`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-pickle

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/byom_handler/byom_handler.py:402-402`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-pickle

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/byom_handler/byom_handler.py:411-411`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-pickle

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/byom_handler/byom_handler.py:419-419`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-pickle

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/byom_handler/byom_handler.py:423-423`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-pickle

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/byom_handler/proc_wrapper.py:51-51`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-pickle

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/byom_handler/proc_wrapper.py:55-55`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.exec-detected.exec-detected

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/byom_handler/proc_wrapper.py:80-80`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/dspy_handler/dspy_handler.py:90-90`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/dspy_handler/dspy_handler.py:93-93`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/dspy_handler/dspy_handler.py:124-124`  
**Type:** security  
**Source:** semgrep  



### python.boto3.security.hardcoded-token.hardcoded-token

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/dynamodb_handler/connection_args.py:35-39`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/empress_handler/empress_handler.py:197-197`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/flaml_handler/flaml_handler.py:33-33`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/flaml_handler/flaml_handler.py:42-42`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/gcs_handler/gcs_handler.py:182-182`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/gcs_handler/gcs_handler.py:218-218`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/gcs_handler/gcs_handler.py:224-224`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/hsqldb_handler/hsqldb_handler.py:186-186`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/ibm_cos_handler/ibm_cos_handler.py:164-166`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/ibm_cos_handler/ibm_cos_handler.py:167-169`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/ibm_cos_handler/ibm_cos_handler.py:177-177`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/ibm_cos_handler/ibm_cos_handler.py:198-198`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/ibm_cos_handler/ibm_cos_handler.py:223-225`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/ibm_cos_handler/ibm_cos_handler.py:229-229`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/ingres_handler/ingres_handler.py:197-197`  
**Type:** security  
**Source:** semgrep  



### generic.secrets.security.detected-generic-api-key.detected-generic-api-key

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/instatus_handler/instatus_handler.py:126-126`  
**Type:** security  
**Source:** semgrep  



### generic.secrets.security.detected-generic-api-key.detected-generic-api-key

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/intercom_handler/intercom_handler.py:116-116`  
**Type:** security  
**Source:** semgrep  



### generic.secrets.security.detected-jwt-token.detected-jwt-token

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/libsql_handler/README.md:44-44`  
**Type:** security  
**Source:** semgrep  



### generic.secrets.security.detected-generic-api-key.detected-generic-api-key

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/lightdash_handler/lightdash_handler.py:106-106`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/lightfm_handler/lightfm_handler.py:81-81`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/lightfm_handler/lightfm_handler.py:104-104`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/lightwood_handler/utils.py:25-25`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/lightwood_handler/utils.py:36-36`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/lindorm_handler/lindorm_handler.py:198-198`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/ludwig_handler/ludwig_handler.py:42-42`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/ludwig_handler/ludwig_handler.py:45-45`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/monetdb_handler/utils/monet_get_id.py:17-17`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/monetdb_handler/utils/monet_get_id.py:42-42`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/mssql_handler/mssql_handler.py:321-321`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/neuralforecast_handler/neuralforecast_handler.py:63-63`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/neuralforecast_handler/neuralforecast_handler.py:64-64`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/neuralforecast_handler/neuralforecast_handler.py:65-65`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/neuralforecast_handler/neuralforecast_handler.py:104-104`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/neuralforecast_handler/neuralforecast_handler.py:105-105`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/neuralforecast_handler/neuralforecast_handler.py:106-106`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.eval-detected.eval-detected

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/openbb_handler/openbb_tables.py:93-93`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/oracle_handler/oracle_handler.py:255-255`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/pgvector_handler/pgvector_handler.py:584-591`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/phoenix_handler/phoenix_handler.py:208-208`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/popularity_recommender_handler/popularity_recommender_handler.py:48-48`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/popularity_recommender_handler/popularity_recommender_handler.py:56-56`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/postgres_handler/postgres_handler.py:501-501`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/postgres_handler/postgres_handler.py:528-528`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/postgres_handler/postgres_handler.py:531-536`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/postgres_handler/postgres_handler.py:540-540`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/postgres_handler/postgres_handler.py:567-567`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/postgres_handler/postgres_handler.py:568-568`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/redshift_handler/tests/test_redshift_handler.py:49-49`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/redshift_handler/tests/test_redshift_handler.py:53-53`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/redshift_handler/tests/test_redshift_handler.py:55-55`  
**Type:** security  
**Source:** semgrep  



### python.boto3.security.hardcoded-token.hardcoded-token

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/s3_handler/connection_args.py:41-47`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/s3_handler/s3_handler.py:150-150`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/s3_handler/s3_handler.py:151-151`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/s3_handler/s3_handler.py:155-155`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/s3_handler/s3_handler.py:163-163`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/s3_handler/s3_handler.py:249-249`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/s3_handler/s3_handler.py:285-285`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/s3_handler/s3_handler.py:291-291`  
**Type:** security  
**Source:** semgrep  



### generic.secrets.security.detected-generic-secret.detected-generic-secret

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/salesforce_handler/connection_args.py:45-45`  
**Type:** security  
**Source:** semgrep  



### generic.secrets.security.detected-generic-api-key.detected-generic-api-key

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/sap_erp_handler/sap_erp_handler.py:159-159`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/snowflake_handler/snowflake_handler.py:258-258`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/statsforecast_handler/statsforecast_handler.py:120-120`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/statsforecast_handler/statsforecast_handler.py:121-121`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/statsforecast_handler/statsforecast_handler.py:135-135`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/statsforecast_handler/statsforecast_handler.py:136-136`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/statsforecast_handler/statsforecast_handler.py:148-148`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/statsforecast_handler/statsforecast_handler.py:149-149`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/statsforecast_handler/statsforecast_handler.py:161-161`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/statsforecast_handler/statsforecast_handler.py:162-162`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/tpot_handler/tpot_handler.py:49-49`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/tpot_handler/tpot_handler.py:50-50`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/tpot_handler/tpot_handler.py:58-58`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-dill

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/handlers/tpot_handler/tpot_handler.py:59-59`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.avoid-pyyaml-load.avoid-pyyaml-load

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/libs/api_handler_generator.py:94-94`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.non-literal-import.non-literal-import

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/libs/ml_handler_process/create_engine_process.py:9-9`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.non-literal-import.non-literal-import

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/libs/ml_handler_process/create_validation_process.py:7-7`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.non-literal-import.non-literal-import

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/libs/ml_handler_process/describe_process.py:53-53`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.non-literal-import.non-literal-import

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/libs/ml_handler_process/func_call_process.py:7-7`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.non-literal-import.non-literal-import

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/libs/ml_handler_process/learn_process.py:87-87`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.non-literal-import.non-literal-import

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/libs/ml_handler_process/predict_process.py:14-14`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.non-literal-import.non-literal-import

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/libs/ml_handler_process/update_engine_process.py:9-9`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.non-literal-import.non-literal-import

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/libs/ml_handler_process/update_process.py:7-7`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.non-literal-import.non-literal-import

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/libs/process_cache.py:31-31`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/libs/storage_handler.py:63-63`  
**Type:** security  
**Source:** semgrep  



### python.jwt.security.unverified-jwt-decode.unverified-jwt-decode

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/utilities/handlers/auth_utilities/snowflake/snowflake_jwt_gen.py:136-136`  
**Type:** security  
**Source:** semgrep  



### python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/integrations/utilities/rag/loaders/vector_store_loader/pgvector.py:181-188`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/interfaces/agents/utils/data_catalog_builder.py:179-179`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/interfaces/agents/utils/data_catalog_builder.py:201-201`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/interfaces/agents/utils/data_catalog_builder.py:241-241`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/interfaces/agents/utils/data_catalog_builder.py:272-272`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.non-literal-import.non-literal-import

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/interfaces/database/integrations.py:775-775`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-pickle

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/interfaces/query_context/context_controller.py:210-210`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-pickle

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/interfaces/query_context/context_controller.py:240-240`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.exec-detected.exec-detected

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/migrations/versions/2021-11-30_17c3d2384711_init.py:172-172`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.insecure-transport.requests.request-with-http.request-with-http

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/utilities/auth.py:18-18`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.insecure-transport.requests.request-with-http.request-with-http

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/utilities/auth.py:21-21`  
**Type:** security  
**Source:** semgrep  



### trailofbits.python.pickles-in-pandas.pickles-in-pandas

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/utilities/cache.py:164-164`  
**Type:** security  
**Source:** semgrep  



### trailofbits.python.pickles-in-pandas.pickles-in-pandas

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/utilities/cache.py:180-180`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-pickle

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/utilities/ml_task_queue/producer.py:58-58`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-pickle

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/utilities/ml_task_queue/utils.py:23-23`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.deserialization.pickle.avoid-pickle

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/utilities/ml_task_queue/utils.py:35-35`  
**Type:** security  
**Source:** semgrep  



### python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/mindsdb/utilities/render/sqlalchemy_render.py:283-283`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.exec-detected.exec-detected

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/setup.py:26-26`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.subprocess-shell-true.subprocess-shell-true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/scripts/check_requirements.py:253-253`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.exec-detected.exec-detected

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor/test_api_handler.py:21-21`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor/test_executor.py:643-643`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor/test_executor.py:650-650`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor/test_executor.py:664-664`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor/test_executor.py:685-685`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor/test_executor.py:697-697`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor/test_executor.py:709-709`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor/test_executor.py:1261-1261`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor/test_executor.py:1284-1284`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor/test_executor.py:1295-1300`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor/test_executor.py:1335-1335`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor/test_executor.py:1360-1365`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor_test_base.py:135-135`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor_test_base.py:136-136`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor_test_base.py:350-350`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor_test_base.py:356-356`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/executor_test_base.py:358-358`  
**Type:** security  
**Source:** semgrep  



### python.boto3.security.hardcoded-token.hardcoded-token

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/handlers/test_dynamodb.py:23-27`  
**Type:** security  
**Source:** semgrep  



### generic.secrets.security.detected-generic-secret.detected-generic-secret

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/handlers/test_ms_teams.py:33-33`  
**Type:** security  
**Source:** semgrep  



### generic.secrets.security.detected-generic-secret.detected-generic-secret

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/handlers/test_ms_teams.py:42-42`  
**Type:** security  
**Source:** semgrep  



### generic.secrets.security.detected-generic-secret.detected-generic-secret

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/handlers/test_ms_teams.py:200-200`  
**Type:** security  
**Source:** semgrep  



### python.boto3.security.hardcoded-token.hardcoded-token

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/handlers/test_s3.py:28-33`  
**Type:** security  
**Source:** semgrep  



### generic.secrets.security.detected-generic-secret.detected-generic-secret

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/handlers/test_salesforce.py:30-30`  
**Type:** security  
**Source:** semgrep  



### generic.secrets.security.detected-generic-secret.detected-generic-secret

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/handlers/test_salesforce.py:136-136`  
**Type:** security  
**Source:** semgrep  



### generic.secrets.security.detected-generic-secret.detected-generic-secret

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/handlers/test_salesforce.py:173-173`  
**Type:** security  
**Source:** semgrep  



### generic.secrets.security.detected-generic-secret.detected-generic-secret

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/handlers/test_salesforce.py:210-210`  
**Type:** security  
**Source:** semgrep  



### generic.secrets.security.detected-generic-secret.detected-generic-secret

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/handlers/test_salesforce.py:251-251`  
**Type:** security  
**Source:** semgrep  



### generic.secrets.security.detected-generic-secret.detected-generic-secret

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/handlers/test_salesforce.py:290-290`  
**Type:** security  
**Source:** semgrep  



### generic.secrets.security.detected-generic-secret.detected-generic-secret

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/handlers/test_salesforce.py:332-332`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.logging.logger-credential-leak.python-logger-credential-disclosure

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unit/utilities/test_log_sanitizer.py:56-56`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.insecure-transport.requests.request-with-http.request-with-http

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unused/integration/a2a/test_a2a_streaming.py:120-120`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.insecure-transport.requests.request-with-http.request-with-http

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unused/integration/a2a/test_a2a_streaming.py:354-354`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unused/integration/knowledge_bases/test_knowledge_bases.py:108-108`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unused/integration/knowledge_bases/test_knowledge_bases.py:110-110`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unused/unit/handler_tests/test_pgvector_handler.py:34-34`  
**Type:** security  
**Source:** semgrep  



### python.lang.security.audit.formatted-sql-query.formatted-sql-query

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unused/unit/handler_tests/test_pgvector_handler.py:38-38`  
**Type:** security  
**Source:** semgrep  



### python.django.security.injection.path-traversal.path-traversal-open.path-traversal-open

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/mindsdb/tests/unused/unit/handler_tests/test_rag_pipelines.py:38-38`  
**Type:** security  
**Source:** semgrep  



### Potential inefficiency in JSON payload processing

**Location:** `mindsdb/api/a2a/agent.py:108-138`  
**Type:** performance  
**Source:** performance_analysis  

The new logic for transforming chunks from HTTP endpoint format to A2A format involves multiple conditional checks and data copying, which could be optimized for better performance.

### Removal of skills-related functionality

**Location:** `mindsdb/api/executor/command_executor.py`  
**Type:** performance  
**Source:** performance_analysis  

The removal of skills-related commands and their handling could lead to unused code paths or libraries that are no longer needed, suggesting an opportunity for codebase optimization.

### Unused variable after removal of functionality

**Location:** `mindsdb/api/executor/command_executor.py:517`  
**Type:** logic  
**Source:** logic_analysis  

After the removal of certain functionalities, some variables are declared but never used, leading to dead code.

### Removed functionality not documented

**Location:** `mindsdb/api/executor/command_executor.py:662`  
**Type:** other  
**Source:** documentation_analysis  

The removal of skills-related functionality is not documented in the PR description or code comments.

### Missing unit tests for removed tokenizer loading

**Location:** `mindsdb/__main__.py:341-355`  
**Type:** other  
**Source:** test_analysis  

The removal of tokenizer loading logic in __main__.py lacks corresponding unit tests to ensure that the removal does not impact the initialization process negatively.

### No tests for handling removal of langchain handler

**Location:** `default_handlers.txt:3-4`  
**Type:** other  
**Source:** test_analysis  

The removal of the langchain handler from default_handlers.txt is not accompanied by tests to verify that the system behaves as expected without it.


## 💬 Nits

### [F401] Style violation

**Location:** `sql.py:272`  
**Type:** style  
**Source:** ruff  

`pandas` imported but unused

### [F541] Style violation

**Location:** `chart_agent.py:88`  
**Type:** style  
**Source:** ruff  

f-string without any placeholders

**Suggested fix:**
```
"ChartAgent.generate_chart_config: Sending prompt to LLM"
```

### String concatenation in loop

**Location:** `diff:line_392`  
**Type:** performance  
**Source:** static_analysis  

Consider using list append and join() for better performance.

### String concatenation in loop

**Location:** `diff:line_1080`  
**Type:** performance  
**Source:** static_analysis  

Consider using list append and join() for better performance.

### String concatenation in loop

**Location:** `diff:line_2406`  
**Type:** performance  
**Source:** static_analysis  

Consider using list append and join() for better performance.

