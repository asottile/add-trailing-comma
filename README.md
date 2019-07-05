[![Build Status](https://dev.azure.com/asottile/asottile/_apis/build/status/asottile.add-trailing-comma?branchName=master)](https://dev.azure.com/asottile/asottile/_build/latest?definitionId=3&branchName=master)
[![Azure DevOps coverage](https://img.shields.io/azure-devops/coverage/asottile/asottile/3/master.svg)](https://dev.azure.com/asottile/asottile/_build/latest?definitionId=3&branchName=master)

add-trailing-comma
==================

A tool (and pre-commit hook) to automatically add trailing commas to calls and
literals.

## Installation

`pip install add-trailing-comma`

## As a pre-commit hook

See [pre-commit](https://github.com/pre-commit/pre-commit) for instructions

Sample `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/asottile/add-trailing-comma
    rev: v1.4.0
    hooks:
    -   id: add-trailing-comma
```

## multi-line method invocation style -- why?

```python
# Sample of *ideal* syntax
function_call(
    argument,
    5 ** 5,
    kwarg=foo,
)
```

- the initial paren is at the end of the line
- each argument is indented one level further than the function name
- the last parameter (unless the call contains an unpacking
  (`*args` / `**kwargs`)) has a trailing comma

This has the following benefits:

- arbitrary indentation is avoided:

    ```python
    # I hear you like 15 space indents
    # oh your function name changed? guess you get to reindent :)
    very_long_call(arg,
                   arg,
                   arg)
    ```
- adding / removing a parameter preserves `git blame` and is a minimal diff:

    ```diff
     # with no trailing commas
     x(
    -    arg
    +    arg,
    +    arg2
     )
    ```

    ```diff
     # with trailing commas
     x(
         arg,
    +    arg2,
     )
    ```


## Implemented features

### trailing commas for function calls

```diff
 x(
     arg,
-    arg
+    arg,
 )
```

### trailing commas for function calls with unpackings

If `--py35-plus` is passed, `add-trailing-comma` will also perform the
following change:

```diff
 x(
-    *args
+    *args,
 )
 y(
-    **kwargs
+    **kwargs,
 )
```

Note that this would cause a **`SyntaxError`** in earlier python versions.

### trailing commas for tuple / list / dict / set literals

```diff
 x = [
-    1, 2, 3
+    1, 2, 3,
 ]
```

### trailing commas for function definitions

```diff
 def func(
         arg1,
-        arg2
+        arg2,
 ):
```

### trailing commas for function definitions with unpacking arguments

If `--py36-plus` is passed, `add-trailing-comma` will also perform the
following change:

```diff
 def f(
-    *args
+    *args,
 ): pass


 def g(
-    **kwargs
+    **kwargs,
 ): pass


 def h(
-    *, kw=1
+    *, kw=1,
 ): pass
```

Note that this would cause a **`SyntaxError`** in earlier python versions.

### trailing commas for `from` imports

```diff
 from os import (
     path,
-    makedirs
+    makedirs,
 )
```

### trailing comma for class definitions

```diff
 class C(
     Base1,
-    Base2
+    Base2,
 ):
     pass
```

### unhug trailing paren

```diff
 x(
     arg1,
-    arg2)
+    arg2,
+)
```

### unhug leading paren

```diff
-function_name(arg1,
-              arg2)
+function_name(
+    arg1,
+    arg2,
+)
```

### match closing brace indentation

```diff
 x = [
     1,
     2,
     3,
-    ]
+]
```

### remove unnecessary commas

yes yes, I realize the tool is called `add-trailing-comma` :laughing:

```diff
-[1, 2, 3,]
-[1, 2, 3, ]
+[1, 2, 3]
+[1, 2, 3]
```
