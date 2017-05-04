`cssdecl` Python CSS declaration computer
-----------------------------------------

This package provides basic computation of CSS declarations in order to:

* handle overwriting of properties
* expand shorthands like `border-width: 0 5px` into `border-top-width: 0`, `border-right-width: 5px`, `border-bottom-width: 0`, `border-left-width: 5px`
* (TODO!) expand shorthands like `font: 5px sans-serif bold` into `font-family: sans-serif`, `font-size: 5px`, `font-weight: bold`
* resolve sizes to a common unit (i.e. pt)
* resolve `inherit` given some inherited declarations

It does not process CSS selectors and their applicability to elements, including specificity.

Some properties that are not shorthands in CSS 2.2 become
shorthands in CSS 3, such as `text-decoration`. We therefore
hope to provide CSS22Resolver and CSS3Resolver.


This was first developed for use in Pandas_ (`#15530 <https://github.com/pandas-dev/pandas/pull/15530>`_).
Issues will continue to be prioritised to improve CSS support there, in the absence of other clear use-cases.


.. _Pandas: http://pandas.pydata.org
