"""
:synopsis: Python/Javascript glue for the AnserIndicus library.
:platform: Tested on Mac OSX and Linux, Windows theoretically possible

This depends on :mod:`anser_indicus` and on :mod:`tornado`.

This package contains the following:
    1. A Python API that interacts with `AnserIndicus`
    2. A Websocket server that serves as glue between the Python and Javascript sides
    3. A Javascript API that mirrors the Python API, in that the function calls look the same. Returns are asynchronous.

.. moduleauthor:: Andrew B Godbehere
"""


