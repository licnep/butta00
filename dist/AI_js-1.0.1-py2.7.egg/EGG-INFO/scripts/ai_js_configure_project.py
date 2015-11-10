"""
Helper script, make a new configuration file for a websocket server instance.

Script proceeds as follows:

    * Asks for name of server instance, allows option to run with different configurations. Suppose it is called ``foo``
    * Creates a configuration file in current directory, ``foo.cfg``
    * Configuration file maintains the following information which you must specify before running the webserver:

        * ``application_name``: *specify arbitrary name for your web app*
        * ``port``: *numerical port on which to run websocket*
        * ``application_path``: *root directory of the web app*
        * ``authentication_root_path``: *optional - root directory of all authenticated content*
        * ``static_path``: *directory where all static files, like css, are stored*
        * ``error_page_path``: *directory where all error pages (like 404) are stored*



.. moduleauthor:: Andrew B Godbehere
"""
from ConfigParser import SafeConfigParser
from os import path
from anser_indicus.utilities.colors import bcolors

if __name__ == "__main__":
    cfgname = raw_input("Name of server instance > ")

    # test to make sure that server name doesn't already exist
    if path.exists(cfgname+'.cfg'):
        print bcolors.HEADER+"Config file already exists!"+bcolors.ENDC
        exit(1)

    # if it doesn't exist, create an initial configuration file
    cfgparser = SafeConfigParser(allow_no_value=True)

    cfgparser.add_section("server_settings")
    cfgparser.set("server_settings", "# Use RELATIVE paths for all entries.")
    cfgparser.set("server_settings", "application_name", "# set a name for your server application.")
    cfgparser.set("server_settings", "port", "# set this to the desired port for the tornado server.")
    cfgparser.set("server_settings", "application_path", "# this should be the root directory of your web app.")
    cfgparser.set("server_settings", "authentication_root_path", "# optional: any sub-directory must authenticate"
                                                                 " first.")
    cfgparser.set("server_settings", "static_path", "# this points to the directory where all static files are kept.")
    cfgparser.set("server_settings", "error_page_path", "# point this to a directory where all error pages are kept.")
    cfgparser.set("server_settings", "js_api_path", path.join("%(static_path)s", "js"))
    cfgparser.set("server_settings", "auth_type", "# Google, Simple, or None")
    cfgparser.set("server_settings", "cookie_name", "# name of cookie for web app authentication")
    cfgparser.set("server_settings", "server_prefix", "/")
    fout = open(cfgname+".cfg", 'wb')
    cfgparser.write(fout)
    print bcolors.BOLD+bcolors.OKGREEN + "Your config file template is saved as " + cfgname+".cfg"+bcolors.ENDC
    '''
    examplepath = resource_filename("ai_js", "js_api")
    fnames = [x for x in listdir(examplepath) if x.rsplit('.', 1)[-1] == 'js']
    for f in fnames:
        fixedf = f.rsplit('.', 1)[0]+".py"
        copyfile(path.join(examplepath, f), path.join(install_path, "examples", fixedf))
    '''