"""
Utilities for interacting with the ``anser_indicus`` time representation.

:var TIME_INCREMENT_CODES: (`dict`)

    * 'ds': 'tenth of a second'
    * 's': 'second'
    * 'min': 'minute'
    * 'h': 'hour'
    * 'd': 'day'
    * 'w': 'week'
    * 'm': 'month'
    * 'q': 'quarter'
    * 'y': 'year'
    * 'a': 'all'

"""
from ai_js.callbacks import JS_CONST

# constant
TIME_INCREMENT_CODES = JS_CONST({
    'ds': 'tenth of a second',
    's': 'second',
    'min': 'minute',
    'h': 'hour',
    'd': 'day',
    'w': 'week',
    'm': 'month',
    'q': 'quarter',
    'y': 'year',
    'a': 'all'
})
