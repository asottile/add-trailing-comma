[![build status](https://github.com/asottile/add-trailing-comma/actions/workflows/main.yml/badge.svg)](https://github.com/asottile/add-trailing-comma/actions/workflows/main.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/asottile/add-trailing-comma/main.svg)](https://results.pre-commit.ci/latest/github/asottile/add-trailing-comma/main)

add-trailing-comma
==================

A tool (and pre-commit hook) to automatically add trailing commas to calls and
literals.

## Installation

```bash
pip install add-trailing-comma
```

## As a pre-commit hook

See [pre-commit](https://github.com/pre-commit/pre-commit) for instructions

Sample `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/asottile/add-trailing-comma
    rev: v3.2.0
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

```diff
 async def func(
         arg1,
-        arg2
+        arg2,
 ):
```

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

### trailing comma for with statement

```diff
 with (
         open('f1', 'r') as f1,
-        open('f2', 'w') as f2
+        open('f2', 'w') as f2,
 ):
     pass
```

### trailing comma for match statement

```diff
 match x:
     case A(
        1,
-       2
+       2,
     ):
        pass
     case (
        1,
-       2
+       2,
     ):
        pass
     case [
        1,
-       2
+       2,
     ]:
        pass
     case {
        'x': 1,
-       'y': 2
+       'y': 2,
     }:
        pass
```


### trailling comma for PEP-695 type aliases

```diff
 def f[
-    T
+    T,
 ](x: T) -> T:
     return x
```

```diff
 class A[
-    K
+    K,
 ]:
     def __init__(self, x: T) -> None:
         self.x = x
```

```diff
 type ListOrSet[
-     T
+     T,
] = list[T] | set[T]
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
