[![Build Status](https://travis-ci.org/asottile/add-trailing-comma.svg?branch=master)](https://travis-ci.org/asottile/add-trailing-comma)
[![Coverage Status](https://coveralls.io/repos/github/asottile/add-trailing-comma/badge.svg?branch=master)](https://coveralls.io/github/asottile/add-trailing-comma?branch=master)

add-trailing-comma
=========

A tool (and pre-commit hook) to automatically add trailing commas to calls and
literals.

## Installation

`pip install add-trailing-comma`


## As a pre-commit hook

See [pre-commit](https://github.com/pre-commit/pre-commit) for instructions

Sample `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/asottile/add-trailing-comma
    sha: v0.2.1
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

If `--py35-plus` is passed (or python3.5+ syntax is automatically detected),
`add-trailing-comma` will also perform the following change:

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


## Planned features

### trailing commas for function definitions

```diff
 def func(
         arg1,
-        arg2
+        arg2,
 ):
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
