"""
Create the secret key used for authentication.

base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)
"""

import base64
import uuid
from os import path, mkdir


def make_secret(filename):
    s = base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)
    f = open(filename, 'wb')
    f.write(s)
    f.close()    

if __name__ == "__main__":
    if not path.isdir("auth"):
        mkdir("auth")

    make_secret(path.join("auth", "secret.txt"))
    

