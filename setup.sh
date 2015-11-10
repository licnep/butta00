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

gecho() {
    #echo in green color
    echo "$(tput setaf 2)$1$(tput sgr 0)"
}

#Anaconda:
if [[ `which python` != *"anaconda"* ]]
then
    gecho "==== Downloading Anaconda ===="
    #wget -c https://3230d63b5fc54e62148e-c95ac804525aac4b6dba79b00b39d1d3.ssl.cf1.rackcdn.com/Anaconda2-2.4.0-Linux-x86_64.sh #-c to continue download if it was interrupted
    gecho "==== Installing Anaconda ===="
    bash ./Anaconda2-2.4.0-Linux-x86_64.sh -b #batch mode, automatically accepts license
    gecho "Editing .bashrc"
    if ! grep 'anaconda' ~/.bashrc
    then
        echo "export PATH=\"$HOME/anaconda2/bin:$PATH\"" >> ~/.bashrc
    fi
    export PATH="$HOME/anaconda2/bin:$PATH"
else
    gecho "Anaconda already installed."
fi

#APSW:
if ! python -c "import apsw"
then
    gecho "==== Installing apsw ===="
    cd ./dist/apsw-3.8.8.2-r1 && python setup.py fetch --all --missing-checksum-ok build --enable-all-extensions install
    cd ../..
else
    gecho "APSW already installed."
fi

#Anser Indicus:
if ! python -c "import anser_indicus"
then
    gecho "==== Installing anser_indicus ===="
    easy_install ./dist/anser_indicus-1.1.11-py2.7-linux-x86_64.egg
else
    gecho "Anser Indicus already installed."
fi

#AI_js:
if ! python -c "import ai_js"
then
    gecho "==== Installing AI_js ===="
    easy_install ./dist/AI_js-1.0.1-py2.7.egg
else
    gecho "AI_js already installed."
fi

#JDK:
sudo apt-get install -y openjdk-7-jdk

#Jnius
if ! python -c "import jnius"
then
    gecho "==== Installing pyjnius ===="
    pip install jnius
else
    gecho "pyjnius already installed."
fi

#add to path
if ! grep 'butta' ~/.bashrc
then
    gecho "adding ./bin to .bashrc"
    echo "export PATH=\"`pwd`/bin:$PATH\"" >> ~/.bashrc
fi
export PATH="`pwd`/bin:$PATH"

gecho "INSTALLATION SUCCESSFUL!"

