``cssdecl`` Python CSS declaration computer
-------------------------------------------

|version| |py-versions|

|build| |docs| |coverage|


This package provides basic computation of CSS declarations in order to:

* handle overwriting of properties

    >>> from cssdecl import CSS22Resolver
    >>> resolve = CSS22Resolver().resolve_string
    >>> resolve('font-size: 10pt; font-size: 12pt')
    {'font-size': '12pt'}

* expand shorthands like `border-width: 0 5pt`

    >>> resolved = resolve('border-width: 0 5pt')
    >>> resolved.pop('border-left-width')
    '5pt'
    >>> resolved.pop('border-right-width')
    '5pt'
    >>> resolved.pop('border-bottom-width')
    '0pt'
    >>> resolved.pop('border-top-width')
    '0pt'
    >>> resolved
    {}

* (TODO!) expand shorthands like `font: 5px sans-serif bold` into `font-family: sans-serif`, `font-size: 5px`, `font-weight: bold`
* resolve sizes to a common unit (i.e. pt)

    >>> resolve('font-size: 20px')
    {'font-size': '15pt'}
    >>> resolve('font-size: 1em')
    {'font-size': '12pt'}
    >>> resolve('font-size: 1em', inherited={'font-size': '20pt'})
    {'font-size': '20pt'}
    >>> resolve('font-size: small')
    {'font-size': '9.600000pt'}

* resolve `inherit` given some inherited declarations

    >>> resolve('color: red; color: inherit', inherited={'color': 'blue'})
    {'color': 'blue'}

Some properties that are not shorthands in CSS 2.2 become
shorthands in CSS 3, such as `text-decoration`. We therefore
hope to provide :class:`cssdecl.CSS22Resolver` and :class:`cssdecl.CSS3Resolver`.

This module does *not* process CSS selectors (e.g. ``#some-id > * > div.some-class``) and their applicability to elements, including specificity (e.g. ``!important``).

This was first developed for use in Pandas_ (`#15530 <https://github.com/pandas-dev/pandas/pull/15530>`_).
Issues will continue to be prioritised to improve CSS support there, in the absence of other clear use-cases.


.. _Pandas: http://pandas.pydata.org


.. |py-versions| image:: https://img.shields.io/pypi/pyversions/Django.svg
    :alt: Python versions supported

.. |version| image:: https://badge.fury.io/py/cssdecl.svg
    :alt: Latest version on PyPi
    :target: https://badge.fury.io/py/cssdecl

.. |build| image:: https://travis-ci.org/jnothman/cssdecl.svg?branch=master
    :alt: Travis CI build status
    :scale: 100%
    :target: https://travis-ci.org/jnothman/cssdecl

.. |coverage| image:: https://coveralls.io/repos/github/jnothman/cssdecl/badge.svg
    :alt: Test coverage
    :target: https://coveralls.io/github/jnothman/cssdecl

.. |docs| image:: https://readthedocs.org/projects/cssdecl/badge/?version=latest
     :alt: Documentation Status
     :scale: 100%
     :target: https://cssdecl.readthedocs.io/en/latest/?badge=latest
