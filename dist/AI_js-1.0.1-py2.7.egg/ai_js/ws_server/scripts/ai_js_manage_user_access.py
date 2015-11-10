"""
Manage authentication privileges in system
"""
from anser_indicus.data.database_controller import DatabaseController
from anser_indicus.utilities.menus import crude_text_menu

import sys
import getopt
from os import path, mkdir


def add_user():
    authdb = DatabaseController(path.join("auth", "sumupauth.db"), force=True)
    authdb.primary_cursor.execute("CREATE TABLE IF NOT EXISTS permits(email text UNIQUE);")

    title = "Specify a user e-mail address for which to grant access"
    while True:
        user_email = raw_input(title+"> ")
        try:
            authdb.primary_cursor.execute("INSERT OR IGNORE INTO permits VALUES(?);", (user_email,))
        except:
            print "Failed to add user", user_email, "!"
        else:
            print "Added user", user_email

        to_continue = raw_input("Add another? [y/n] > ")
        if to_continue.lower() != 'y':
            break


def remove_user():
    authdb = DatabaseController(path.join("auth", "sumupauth.db"), force=True)
    authdb.primary_cursor.execute("CREATE TABLE IF NOT EXISTS permits(email text UNIQUE);")

    title = "Revoke access for a specified user"
    while True:
        authdb.primary_cursor.execute("select email from permits;")
        result = authdb.primary_cursor.fetchall()
        user_list = [x['email'] for x in result]
        selection = crude_text_menu(user_list, title=title)

        if selection == -1:
            break

        targeted_user = user_list[selection]

        try:
            authdb.primary_cursor.execute("DELETE FROM permits WHERE email==?;", (targeted_user,))
        except:
            print "Failed to remove user", targeted_user, "!"
        else:
            print "Removed user", targeted_user


def list_users():
    authdb = DatabaseController(path.join("auth", "sumupauth.db"), force=True)
    authdb.primary_cursor.execute("CREATE TABLE IF NOT EXISTS permits(email text UNIQUE);")

    authdb.primary_cursor.execute("select email from permits;")
    result = authdb.primary_cursor.fetchall()
    user_list = [x['email'] for x in result]
    print "Users:"
    for u in user_list:
        print "    + ", u
    print "-----\n\n"
    x = raw_input("Press enter to continue...")


def main2():
    if not path.isdir("auth"):
        mkdir("auth")

    main_options = ("add user", "remove user", "list users")

    action = ''

    while action != 'q':
        selection = crude_text_menu(main_options, title="Select an Action")
        if selection == -1:
            print "EXIT", exit(1)
        action = main_options[selection][0]

        if action == 'a':
            # add user
            add_user()
        elif action == 'r':
            # remove user
            remove_user()
        elif action == 'l':
            # list user
            list_users()
        else:
            action = 'q'

    print "Goodbye!"


def main(argv):
    if not path.isdir("auth"):
        mkdir("auth")

    adduserlist = []
    removeuserlist = []
    try:
        opts, args = getopt.getopt(argv, 'hla:r:', ["adduser=", "removeuser="])
    except getopt.GetoptError:
        print "ai_js_manage_user_access.py -[la <user(s)> r <user(s)>]"
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print "ai_js_manage_user_access.py -[la <user> r <user>]"
            sys.exit()
        elif opt in ("-a", "adduser="):
            adduserlist = arg.strip().split(',')
        elif opt in ('-r', "removeuser="):
            removeuserlist = arg.strip().split(',')
    
    print "adduserlist:", adduserlist
    print "removeuserlist:", removeuserlist
    
    authdb = DatabaseController(path.join("auth", "sumupauth.db"), force=True)
    authdb.primary_cursor.execute("CREATE TABLE IF NOT EXISTS permits(email text UNIQUE);")
    
    if len(adduserlist) > 0:
        for a in adduserlist:
            try:
                authdb.primary_cursor.execute("INSERT OR IGNORE INTO permits VALUES(?);", (a,))
            except:
                print "Failed to add user", a, "!"
            else:
                print "Added user", a
    
    if len(removeuserlist) > 0:
        for r in removeuserlist:
            try:
                authdb.primary_cursor.execute("DELETE FROM permits WHERE email==?;", (r,))
            except:
                print "Failed to remove user", r, "!"
            else:
                print "Removed user", r
    

if __name__ == "__main__":
    #main(sys.argv[1:])
    main2()
