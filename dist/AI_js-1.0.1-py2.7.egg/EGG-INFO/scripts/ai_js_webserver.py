#!/home/virtualenvs/.virtualenvs/experimental-server/bin/python
"""
Webserver for SumUp applications. Manages HTTP and Websocket communications.

Automatically loads the latest installed ai_js_api on run.

.. note:: requires :mod:`tornado`, :mod:`anser_indicus`

.. moduleauthor:: Andrew B. Godbehere
"""
#import future.moves.http.client as http_client
import sys

import os
from os import makedirs, path, getcwd
from anser_indicus.data.database_controller import DatabaseController
from anser_indicus.utilities.colors import bcolors
from anser_indicus.utilities.menus import crude_text_menu
import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define, options
from ai_js.ws_server.web_socket_handler import WSHandler
from ai_js import generate_ai_js_api
from ConfigParser import SafeConfigParser

define("database_name", default="sumupauth.db", help="name of the authentication database file")


def read_cookie_secret():
    """
    Generate cookie secret once, re-use each time server is started. Useful for debugging, may
    remove when server is deployed.

    secret.txt is generated by a script: utilities/ai_js_generate_cookie_secret.py.
    """
    fobj = open(path.join('auth', "secret.txt"), 'rb')
    s = fobj.read()
    return s


class Application(tornado.web.Application):
    def __init__(self, handlers=None, default_host="", transforms=None, wsgi=False, **settings):
        tornado.web.Application.__init__(self, handlers=handlers, default_host=default_host, transforms=transforms,
                                         wsgi=wsgi, **settings)
        self.authdb = DatabaseController(path.join('auth', options.database_name), force=True)
        self.authdb.primary_cursor.execute("CREATE TABLE IF NOT EXISTS users(email TEXT NOT NULL UNIQUE, "
                                           "name TEXT NOT NULL);")  # email is unique identifier, thanks to Google.


class BaseHandler(tornado.web.RequestHandler):
    @property
    def authdb(self):
        return self.application.authdb

    def get_current_user(self):
        user_id = self.get_secure_cookie(self.cookie_name)
        if not user_id:
            return None
        if user_id.isdigit():
            self.authdb.primary_cursor.execute("SELECT * FROM users WHERE rowid==?;", (int(user_id),))
            return self.authdb.primary_cursor.fetchall()[0]  # provides properties 'email' and 'name'
        else:
            return user_id


class AuthLoginHandler_None(BaseHandler):
    def get(self):
        print "GET AUTHENTICATING NONE"
        self.set_secure_cookie(self.cookie_name, "Demo User")
        print self.get_argument("next", "/")
        self.redirect(self.get_argument("next", "/"))

    def post(self):
        print "POST AUTHENTICATING NONE"
        #self.set_secure_cookie("sumup_user", "Demo User")
        #self.redirect(self.get_argument("next", "/"))


class AuthLoginHandler_Simple(BaseHandler):
    """
    User offers keycode. If valid, they are authenticated.
    """
    def post(self):
        #cookie = self.get_secure_cookie("sumup_user")
        #if cookie is not None:
        #    yield cookie
        # ask for keycode
        access_keycode = self.get_argument("access_keycode")

        # below is sample HTML for form

        '''
        <form action="/login" method="post">'
                   'Access Key: <input type="text" name="access_keycode">'
                   '<input type="submit" value="keycode">'
                   '</form>
        '''
        self.authdb.primary_cursor.execute("SELECT keycode FROM keycodes where keycode == ?;", (access_keycode, ))
        result = self.authdb.primary_cursor.fetchall()
        if not result:
            self.redirect(self.server_prefix+"sys/noauth.html")
        else:
            self.set_secure_cookie(self.cookie_name, 'Demo User')
            next_arg = self.get_argument("next", "/")
            print "REDIRECTING TO:", next_arg
            self.redirect(self.get_argument("next", "/"))


# noinspection PyUnresolvedReferences
class AuthLoginHandler_Google(BaseHandler, tornado.auth.GoogleMixin):
    @tornado.gen.coroutine
    def get(self):
        print "GOOGLE AUTH"
        cookie = self.get_secure_cookie(self.cookie_name)
        if cookie is not None:
            yield cookie
        if self.get_argument("openid.mode", None):
            user = yield self.get_authenticated_user()
            if not user:
                raise tornado.web.HTTPError(500, "Google auth failed")
                                    
            print "USER EMAIL:", user["email"]
            self.authdb.primary_cursor.execute("SELECT rowid FROM permits WHERE email == ?;", (user["email"],))
            result = self.authdb.primary_cursor.fetchall()
            if result is None or len(result) == 0:
                self.redirect(self.server_prefix+"sys/noauth.html")
                return
                #raise tornado.web.HTTPError(500, "SumUp Analytics is operating under a closed beta.
                # Please try again later.")ConfigParser.Error
            
            self.authdb.primary_cursor.execute("SELECT rowid,* FROM users WHERE email == ?;", (user["email"],))
            
            author = self.authdb.primary_cursor.fetchall()
            print "author:", author
            
            if not author or len(author) == 0:
                self.authdb.primary_cursor.execute("INSERT INTO users VALUES(?,?);", (user["email"], user["name"]))
                
                self.authdb.primary_cursor.execute("SELECT rowid FROM users WHERE email==?;", (user["email"],))
                author_id = self.authdb.primary_cursor.fetchall()[0]['rowid']
                            
            else:
                author_id = author[0]["rowid"]
            
            print "AUTHORID:", author_id
            #self.set_secure_cookie("sumup_user", str(author_id))
            self.set_secure_cookie(self.cookie_name, str(author_id))
            self.redirect(self.get_argument("next", "/"))
        else:
            yield self.authenticate_redirect()
    

class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie(self.cookie_name)
        self.redirect(self.get_argument("next", "/"))


# noinspection PyUnresolvedReferences
class DemoHandler(BaseHandler):
    def __init__(self, application, request, **kwargs):
        print "initializing the demo handler"
        if 'authentication_root_path' in kwargs:
            self.authentication_root_path = kwargs.pop('authentication_root_path')
        else:
            self.authentication_root_path = None
        super(DemoHandler, self).__init__(application, request, **kwargs)

    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        print "CURRENT_USER:", self.current_user
        
        #print args,kwargs  #@TODO: Use args to render specific pages
        fname = None
        if len(args) > 0:
            #fname = path.join(self.authentication_root_path, path.basename(args[0]))

            fname = path.join(self.authentication_root_path, args[0].strip('/'))
            #fname = path.join(os.path.dirname(__file__), "..", "static", "demos", "auth", path.basename(args[0]))
        
        #print fname
        
        if fname is not None:
            self.render(fname)
        else:        
            email = tornado.escape.xhtml_escape(self.current_user["email"])
            self.write("Hello, "+email)
            #print "HELLO,",email


class HomeHandler(BaseHandler):
    def __init__(self, application, request, **kwargs):
        if 'application_path' in kwargs:
            self.application_path = kwargs.pop('application_path')
        else:
            self.application_path = None
        super(HomeHandler, self).__init__(application, request, **kwargs)

    def get(self, *args, **kwargs):
        if len(args) == 0 or args[0] == "":
            fname = path.join(self.application_path, "index.html")
            with open(fname, 'r') as f:
                self.write(f.read())
            #self.render(path.join(os.path.dirname(__file__), "..", "static", "demos", "index.html"))
        else:
            #print "ARGS:",args[0]
            fname = path.join(self.application_path, path.basename(args[0]))
            #fname = path.join(os.path.dirname(__file__), "..", "static", "demos", path.basename(args[0]))
        
            if fname is not None:
                with open(fname, 'r') as f:
                    self.write(f.read())
                #self.render(fname)


class SysHandler(BaseHandler):
    def __init__(self, application, request, **kwargs):
        if 'error_page_path' in kwargs:
            self.error_page_path = kwargs.pop('error_page_path')
        else:
            self.error_page_path = None
        super(SysHandler, self).__init__(application, request, **kwargs)

    def get(self, *args, **kwargs):
        if len(args) > 0 and args[0] != "":        
            #print "ARGS:",args[0]
            fname = path.join(self.error_page_path, path.basename(args[0]))
            #fname = path.join(os.path.dirname(__file__), "..", "static", "demos", path.basename(args[0]))
        
            if fname is not None:
                self.render(fname)


def run_webserver(webcfgfile, copy=True):
    if not path.exists(webcfgfile):
        print bcolors.HEADER+"Config file not found."+bcolors.ENDC

    # at this point, webcfgfile is the name of an existing config file
    cfgparser = SafeConfigParser()
    result = cfgparser.read(webcfgfile)
    if result != [webcfgfile]:
        print bcolors.HEADER+"Could not read config file."+bcolors.ENDC
        exit(1)

    portnum = cfgparser.get("server_settings", "port")
    if not portnum.isdigit():
        print bcolors.HEADER+"Invalid port setting"+bcolors.ENDC
        exit(1)
    try:
        portnum = int(portnum)
    except ValueError:
        print bcolors.HEADER+"Invalid port setting"+bcolors.ENDC
        exit(1)
    # now, portnum is an integer

    application_name = cfgparser.get("server_settings", "application_name")

    application_path = cfgparser.get("server_settings", "application_path")
    if not path.isdir(application_path):
        print bcolors.HEADER+"Application path does not exist"+bcolors.ENDC
        exit(1)
    print "APPLICATION PATH:", application_path
    authentication_root_path = cfgparser.get("server_settings", "authentication_root_path")
    if not path.isdir(authentication_root_path):
        print bcolors.HEADER+"Authentication root path does not exist"+bcolors.ENDC
        exit(1)

    static_path = cfgparser.get("server_settings", "static_path")
    if not path.isdir(static_path):
        print bcolors.HEADER+"Static path does not exist"+bcolors.ENDC
        exit(1)

    error_page_path = cfgparser.get("server_settings", "error_page_path")
    if not path.isdir(error_page_path):
        print bcolors.HEADER+"Error page path does not exist"+bcolors.ENDC
        exit(1)

    js_api_path = cfgparser.get("server_settings", "js_api_path")
    if not path.isdir(js_api_path):
        makedirs(js_api_path)
    # copy the js_api over
    generate_ai_js_api.copy_to(js_api_path)

    auth_type = cfgparser.get("server_settings", "auth_type")
    cookie_name = cfgparser.get("server_settings", "cookie_name")
    server_prefix = cfgparser.get("server_settings", "server_prefix")

    if not cookie_name or cookie_name == "":
        cookie_name = "sumup_user"

    print "AUTH TYPE:", auth_type
    if auth_type == "Google":
        auth_class = AuthLoginHandler_Google
        xsrf_cookies = True

        def initialize(BaseHandler):
            BaseHandler.cookie_name = cookie_name
            BaseHandler.server_prefix = server_prefix
        BaseHandler.initialize = initialize

        def ws_initialize(WSHandler):
            WSHandler.cookie_name = cookie_name
        WSHandler.initialize = ws_initialize

    elif auth_type == "Simple":
        auth_class = AuthLoginHandler_Simple
        xsrf_cookies = False

        def initialize(BaseHandler):
            BaseHandler.cookie_name = cookie_name
            BaseHandler.server_prefix = server_prefix

        BaseHandler.initialize = initialize
        WSHandler.initialize = initialize

        def get_current_user(BaseHandler):
            print "COOKIE:", BaseHandler.get_secure_cookie(BaseHandler.cookie_name)
            return BaseHandler.get_secure_cookie(BaseHandler.cookie_name)

        BaseHandler.get_current_user = get_current_user
        WSHandler.get_current_user = get_current_user

    else:
        xsrf_cookies = False

        # disable authentication in BaseHandler and WSHandler
        def initialize(BaseHandler):
            BaseHandler.current_user = "demouser"
            BaseHandler.cookie_name = cookie_name
            BaseHandler.server_prefix = server_prefix

        def get_current_user(BaseHandler):
            return BaseHandler.current_user

        BaseHandler.initialize = initialize
        BaseHandler.get_current_user = get_current_user
        WSHandler.initialize = initialize
        WSHandler.get_current_user = get_current_user
        auth_class = AuthLoginHandler_None

    cookie_secret = read_cookie_secret()
    web_application = Application([
        (r"/", HomeHandler, {'application_path': application_path}),
        (r"/"+r"sys/(.*)", SysHandler, {'error_page_path': error_page_path}),  # handle system error pages
        (r"/"+r"demos/auth(.*)", DemoHandler, {'authentication_root_path': authentication_root_path}),
        (r"/auth/login", auth_class),
        (r"/auth/logout", AuthLogoutHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": static_path}),
        (r"/ws", WSHandler)],
        title=application_name,
        xsrf_cookies=xsrf_cookies,
        cookie_secret=cookie_secret,
        login_url=r""+server_prefix+r"auth/login",
        template_path=os.getcwd(),
        debug=True
    )

    http_server = tornado.httpserver.HTTPServer(web_application)
    http_server.listen(portnum)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_webserver(sys.argv[1])
    else:
        files = [f for f in os.listdir('.') if os.path.isfile(f) and f.rsplit('.', 1)[-1] == 'cfg']
        if len(files) == 0:
            print bcolors.HEADER+"No config file in current working directory. Call ai_js_configure_project.py to " \
                                 "make a new config file. Edit the resulting config file before running " \
                                 "this script again."+bcolors.ENDC
            exit(1)

        else:
            # noinspection PyTypeChecker
            result_arg = crude_text_menu(files)
            if result_arg >= 0:
                cfgfile = files[result_arg]
                run_webserver(cfgfile)
            else:
                print bcolors.HEADER+"No config file selected. Goodbye!"+bcolors.ENDC
                exit(1)
