"""
.. module:: generate_ai_js_api
    :synopsis: Script that automatically generates a javascript API to match the Python backend API.

.. moduleauthor:: Andrew B Godbehere

Design
======

This script is designed to read the contents of the :mod:`ai_js.callbacks` package and to create corresponding
javascript files that implement the API on the javascript side. The design is such that the Python call-model is
preserved on the Javascript side.

.. note:: This call model is **asynchronous**. Calling a Javascript function will return immediately, but the message
    is sent via a Websocket connection to the server. Once the Python function is complete, which may take some time, a
    return message is sent back to the client with the results. The Javascript side, therefore, has callbacks. WebApps
    can react to data and analyses by overloading these callbacks.

.. note:: In the time it takes for the server to process a single request, an end-user can send many more messages
    to the server for processing. Due to the fact that some requests *depend* on the results of previous requests, all
    messages are processed through a message queue. Messages, therefore, are **guaranteed to complete in the order
    received**. It should be noted that the reception order *may* be different from transmission order, though this corner
    case has yet to be dealt with.

.. todo:: Deal with messages being received out of order.

Python-side
-----------

To preserve the state of the end-user, all Python function calls accept a required parameter called "connection", which
is a :class:`ai_js.callbacks.connection.connection_state.ConnectionState`. The remaining arguments are
**keyword arguments**, which are the only function arguments exposed to the Javascript side. All of the keyword
arguments have specified defaults, which are implemented as parameter defaults on the Javascript side.

Each Python function returns a dictionary, which is translated into a JSON object to be sent to the client-side
Javascript. The first key of the dictionary is *always* the function name, as the client-side must know which function
call is returning. The actual contents of the return form a JSON object that is passed to the Javascript callback
function.

Example return for function foo: ``{"foo":{"bar":3, "baz":"giraffe}}``. The javascript callback function will receive
an object called "args" with properties "bar" and "baz".


Javascript-side
---------------

Due to the asynchronous call model, every Python function has a corresponding Javascript function AND a corresponding
Javascript callback function.


Example
-------

For example, defining a Python function like

.. code-block:: python

    def ai_js.callbacks.data.foo(connection, a="", b=1):
        result = a+str(b)
        return {"data.foo":{"result":result}}

will result in a javascript call

.. code-block:: json

    ai_python.data.foo(a,b).call_backend();

The callback can be implemented with:

.. code-block:: javascript

    AI_API.DATA.prototype.on_foo = function(args) {
        // Your code goes here. args has one property:
        // args.result
    };


This script will generate the api in a directory within the current working directory. Call it from where you would
like it to be installed.

Usage
=====

On the command-line, run::

    > generate_ai_js_api.py

If your current working path is ``cwd/``, the API will be installed in::

    cwd/ai_js_api/
"""

from os import path, makedirs
from shutil import copyfile
from inspect import getmembers, isfunction, ismodule, getargspec, getdoc
from ai_js.callbacks import analytics, connection, data, utilities, JS_CONST
from pkg_resources import resource_filename
from collections import OrderedDict


def copy_to(js_path):
    # always write the output to a directory named ai_js_api.
    outdir = path.join(js_path, "ai_js_api")
    if not path.exists(outdir):
        makedirs(outdir)

    # copy the main API file over
    master_api_file = resource_filename("ai_js", "anser_indicus_api.js")
    fname = "anser_indicus_api.js"
    copyfile(master_api_file, path.join(outdir, fname))

    for subpackagename, subpackage in {"analytics": analytics, "connection": connection,
                                       "data": data, "utilities": utilities}.iteritems():

        package_contents = dict(getmembers(subpackage, ismodule))
        if not path.exists(path.join(outdir, subpackagename)):
            makedirs(path.join(outdir, subpackagename))

        for curr_mod_name, curr_mod in package_contents.iteritems():
            # here we make the file!
            # inspect each mod to find the functions
            with open(path.join(outdir, subpackagename, curr_mod_name)+".js", 'w') as f:
                # First copy the module high-level doc
                docstring = getdoc(curr_mod)
                f.write("/*\n"+docstring+"\n*/\n\n")
                # Then write the portion of the API dedicated to creating the appropriate javascript objects
                f.write("""if (typeof AI_PYTHON.%s === "undefined") { \n""" % (subpackagename.upper()))
                f.write("""    AI_PYTHON.%s = function(ai_ptr) { \n""" % (subpackagename.upper()))
                f.write("""        this.ai_ptr = ai_ptr; \n""")
                f.write("""    };\n""")
                f.write("""    ai_python.%s = new AI_PYTHON.%s(ai_python);\n""" % (subpackagename.lower(),
                                                                                   subpackagename.upper()))
                f.write("""}\n\n""")

                f.write("""if (typeof AI_PYTHON.%s.%s === "undefined") {\n""" % (subpackagename.upper(),
                                                                                 curr_mod_name.upper()))
                f.write("""    AI_PYTHON.%s.%s = function(ai_ptr) {\n""" % (subpackagename.upper(),
                                                                            curr_mod_name.upper()))
                f.write("""        this.ai_ptr = ai_ptr;\n""")
                f.write("""    };\n""")
                f.write("""    ai_python.%s.%s = new AI_PYTHON.%s.%s(ai_python);\n""" % (subpackagename.lower(),
                                                                                         curr_mod_name.lower(),
                                                                                         subpackagename.upper(),
                                                                                         curr_mod_name.upper()))
                f.write("""}\n\n""")

                f.write("""if (typeof AI_API.%s === "undefined") {\n""" % (subpackagename.upper()))
                f.write("""    AI_API.%s = function() {};\n""" % (subpackagename.upper()))
                f.write("""    ai_api.%s = new AI_API.%s();\n""" % (subpackagename.lower(), subpackagename.upper()))
                f.write("""}\n\n""")

                f.write("""if (typeof AI_API.%s.%s === "undefined") {\n""" % (subpackagename.upper(),
                                                                              curr_mod_name.upper()))
                f.write("""    AI_API.%s.%s = function() {};\n""" % (subpackagename.upper(), curr_mod_name.upper()))
                f.write("""    ai_api.%s.%s = new AI_API.%s.%s();\n""" % (subpackagename.lower(), curr_mod_name.lower(),
                                                                          subpackagename.upper(),
                                                                          curr_mod_name.upper()))
                f.write("""}\n\n""")

                """
                Now, we write out each of the functions
                """
                constants = dict([(k, v) for k, v in curr_mod.__dict__.iteritems() if type(v) is JS_CONST])
                for constname, constval in constants.iteritems():
                    f.write("""if (typeof AI_PYTHON.%s.%s.%s === "undefined") {\n""" % (subpackagename.upper(),
                                                                                        curr_mod_name.upper(),
                                                                                        constname.upper()))

                    f.write("""    AI_PYTHON.%s.%s.prototype.%s = %s;\n}\n""" % (subpackagename.upper(),
                                                                                 curr_mod_name.upper(),
                                                                                 constname.upper(),
                                                                                 repr(constval)))

                #print [(k,v) for k,v in curr_mod.__dict__.iteritems() if type(v) is JS_CONST]

                #print [k for k,v in curr_mod.__dict__.iteritems() if type(v) is dict]
                functions = dict(getmembers(curr_mod, isfunction))
                for fcn_name, fcn in functions.iteritems():
                    if fcn_name[:1] == "_":
                        # then this is a private function, not to be exposed to the api.
                        continue

                    docs = getdoc(fcn)
                    if docs is None:
                        docs = ""
                    argspec = getargspec(fcn)

                    # remove 'connection', which is a python-only parameter, required by all functions.
                    if 'connection' in argspec.args:
                        argspec.args.remove('connection')

                    args = OrderedDict([(a, argspec.defaults[i]) for i, a in enumerate(argspec.args)])

                    f.write("AI_PYTHON.%s.%s.prototype.%s = function(%s) {\n" % (subpackagename.upper(),
                                                                                 curr_mod_name.upper(),
                                                                                 fcn_name, ", ".join(args.keys())))
                    r = ", ".join(["'"+k+"'"+':'+k for k in args.keys()])
                    f.write("    /*\n")
                    for line in docs.split('\n'):
                        f.write("    "+line+"\n")
                    f.write("    */\n")
                    # a = typeof a !== 'undefined' ? a : <default value>
                    for k, d in args.iteritems():
                        if d == '':
                            d = "''"
                        if d == True:
                            d = "true"
                        if d == False:
                            d = "false"

                        f.write("""    %s = (%s !== 'undefined') ? %s : %s;\n""" % (k, k, k, d))

                    if r == '':
                        r = 'null'
                    else:
                        r = "{"+r+"}"
                    f.write("""    this.ai_ptr.json = {"%s.%s.%s" : %s};\n""" % (subpackagename.lower(),
                                                                                 curr_mod_name.lower(), fcn_name, r))
                    # argspec has properties args, varargs, keywords, and defaults.
                    # See https://docs.python.org/2/library/inspect.html.

                    f.write("""    return this.ai_ptr;\n""")
                    f.write("""};\n\n""")

                    f.write("""AI_API.%s.%s.prototype.on_%s = function(args) {\n""" % (subpackagename.upper(),
                                                                                       curr_mod_name.upper(), fcn_name))
                    f.write("""    // overload this function\n""")
                    f.write("""};\n\n""")


if __name__ == "__main__":
    copy_to(".")
