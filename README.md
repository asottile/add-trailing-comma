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
    sha: v0.0.0
    hooks:
    -   id: add-trailing-comma
```

## TODO

`--py35-plus` will append a trailing comma even after `*args` or `**kwargs`
(this is a syntax error in older versions).
