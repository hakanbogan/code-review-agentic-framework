# Code Review

## Summary
Reviewed PR #143: feat: Added iOS support
Changed 0 files (+0/-0)
Found 96 issues requiring attention.

## 🔴 Critical Issues

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/connection.py:210`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/connection.py:235`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/connection.py:265`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:49`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:114`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:167`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:221`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:274`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:315`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:343`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:381`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:413`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:451`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:52`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:85`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:94`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:130`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:159`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:200`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:227`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:262`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:288`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.

### request_with_no_cert_validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/screenshot.py:79`  
**Type:** security  
**Source:** bandit  

Call to requests with verify=False disabling SSL certificate checks, security issue.


## 🟠 Major Issues

### blacklist

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/ios.py:19`  
**Type:** security  
**Source:** bandit  

Consider possible security implications associated with the subprocess module.

**Suggested fix:**
```
--- ios.py
+++ ios.py
@@ -16,7 +16,7 @@
 import subprocess
 
 def execute_shell_command(cmd):
-    return subprocess.check_output(cmd, shell=True)
+    return subprocess.check_output(cmd, shell=False)
```

### start_process_with_partial_path

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/ios.py:63`  
**Type:** security  
**Source:** bandit  

Starting a process with a partial executable path

**Suggested fix:**
```
--- ios.py
+++ ios.py
@@ -60,7 +60,7 @@
 
 def start_process():
     # Original code with issue
-    subprocess.call("someExecutable --option")
+    subprocess.call("/full/path/to/someExecutable --option")
```

### blacklist

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/main.py:19`  
**Type:** security  
**Source:** bandit  

Consider possible security implications associated with the subprocess module.

**Suggested fix:**
```
--- main.py
+++ main.py
@@ -16,7 +16,7 @@
 import subprocess
 
 def execute_command(command):
-    subprocess.call(command, shell=True)
+    subprocess.call(command, shell=False)
```

### start_process_with_partial_path

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/main.py:64`  
**Type:** security  
**Source:** bandit  

Starting a process with a partial executable path

**Suggested fix:**
```
--- a/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/main.py
+++ b/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/main.py
@@ -61,7 +61,7 @@
 
 def some_function():
     # Incorrect way to start a process with a partial path
-    subprocess.Popen("someExecutable --option")
+    subprocess.Popen("/usr/bin/someExecutable --option", shell=True)
```

### start_process_with_partial_path

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/main.py:92`  
**Type:** security  
**Source:** bandit  

Starting a process with a partial executable path

### start_process_with_partial_path

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/main.py:128`  
**Type:** security  
**Source:** bandit  

Starting a process with a partial executable path

### blacklist

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/actions/handler.py:285`  
**Type:** security  
**Source:** bandit  

Use of possibly insecure function - consider using safer ast.literal_eval.

### blacklist

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/connection.py:3`  
**Type:** security  
**Source:** bandit  

Consider possible security implications associated with the subprocess module.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/connection.py:74`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/connection.py:110`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/connection.py:126`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/connection.py:242`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/connection.py:271`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/connection.py:283`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/connection.py:311`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/connection.py:318`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### blacklist

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/device.py:4`  
**Type:** security  
**Source:** bandit  

Consider possible security implications associated with the subprocess module.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/device.py:23`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/device.py:50`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/device.py:70`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/device.py:74`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/device.py:99`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/device.py:136`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/device.py:163`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/device.py:179`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/device.py:203`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### blacklist

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/input.py:4`  
**Type:** security  
**Source:** bandit  

Consider possible security implications associated with the subprocess module.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/input.py:23`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/input.py:49`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/input.py:69`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/input.py:78`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/input.py:100`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### blacklist

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/screenshot.py:5`  
**Type:** security  
**Source:** bandit  

Consider possible security implications associated with the subprocess module.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/screenshot.py:45`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/adb/screenshot.py:58`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### blacklist

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/connection.py:3`  
**Type:** security  
**Source:** bandit  

Consider possible security implications associated with the subprocess module.

### start_process_with_partial_path

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/connection.py:70`  
**Type:** security  
**Source:** bandit  

Starting a process with a partial executable path

### start_process_with_partial_path

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/connection.py:126`  
**Type:** security  
**Source:** bandit  

Starting a process with a partial executable path

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/connection.py:290`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/connection.py:323`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.

### blacklist

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:3`  
**Type:** security  
**Source:** bandit  

Consider possible security implications associated with the subprocess module.

### try_except_pass

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:235`  
**Type:** security  
**Source:** bandit  

Try, Except, Pass detected.

### blacklist

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/screenshot.py:5`  
**Type:** security  
**Source:** bandit  

Consider possible security implications associated with the subprocess module.

### subprocess_without_shell_equals_true

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/screenshot.py:129`  
**Type:** security  
**Source:** bandit  

subprocess call - check for execution of untrusted input.


## 🟡 Minor Issues

### python.lang.security.audit.eval-detected.eval-detected

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/actions/handler.py:285-285`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/connection.py:209-211`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/connection.py:231-236`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/connection.py:265-265`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:48-50`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:114-114`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:167-167`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:221-221`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:274-274`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:315-315`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:343-343`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:380-382`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:413-413`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/device.py:451-451`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:51-53`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:85-85`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:94-94`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:126-131`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:159-159`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:200-200`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:227-227`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:261-263`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/input.py:288-288`  
**Type:** security  
**Source:** semgrep  



### python.requests.security.disabled-cert-validation.disabled-cert-validation

**Location:** `/var/folders/2f/q03m37y143j2h1_2nt8fx18r0000gn/T/code-review-repos/Open-AutoGLM/phone_agent/xctest/screenshot.py:79-79`  
**Type:** security  
**Source:** semgrep  




## 💬 Nits

### [F541] Style violation

**Location:** `basic_usage.py:171`  
**Type:** style  
**Source:** ruff  

f-string without any placeholders

**Suggested fix:**
```
"\n1. Basic Task Example"
```

### [I001] Style violation

**Location:** `ios.py:16`  
**Type:** style  
**Source:** ruff  

Import block is un-sorted or un-formatted

**Suggested fix:**
```
import argparse
import os
import shutil
import subprocess
import sys
from urllib.parse import urlparse

from openai import OpenAI
from phone_agent.agent_ios import IOSAgentConfig, IOSPhoneAgent
from phone_agent.config.apps_ios import list_supported_apps
from phone_agent.model import ModelConfig
from phone_agent.xctest import XCTestConnection, list_devices



```

### [F841] Style violation

**Location:** `ios.py:186`  
**Type:** style  
**Source:** ruff  

Local variable `parsed` is assigned to but never used

### [F541] Style violation

**Location:** `ios.py:204`  
**Type:** style  
**Source:** ruff  

f-string without any placeholders

**Suggested fix:**
```
"   Available models:"
```

### [F541] Style violation

**Location:** `ios.py:231`  
**Type:** style  
**Source:** ruff  

f-string without any placeholders

**Suggested fix:**
```
"   Error: Cannot resolve hostname"
```

