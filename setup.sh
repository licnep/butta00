#!/bin/bash

confirm() {
    #call with a prompt string or use a default
    read -r -p "${1:-Are you sure? [y/N]} " response
    case $response in
        [yY][eE][sS][yY])
                true
                ;; 
            *)
                false
                ;;
    esac
}

if [[ `which python` != *"anaconda"* ]]
then
    echo "==== Downloading Anaconda ===="
    wget -c https://3230d63b5fc54e62148e-c95ac804525aac4b6dba79b00b39d1d3.ssl.cf1.rackcdn.com/Anaconda2-2.4.0-Linux-x86_64.sh #-c to continue download if it was interrupted
    echo "==== Installing Anaconda ===="
    bash ./Anaconda2-2.4.0-Linux-x86_64.sh -b #batch mode, automatically accepts license
    echo "Editing .bashrc"
    echo "export PATH=\"$HOME/anaconda2/bin:$PATH\"" >> ~/.bashrc
else
    echo "Anaconda already installed."
fi

echo "==== Installing apsw ===="
cd ./dist/apsw-3.8.8.2-r1 && python setup.py fetch --all --missing-checksum-ok build --enable-all-extensions install


