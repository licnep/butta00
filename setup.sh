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

recho() {
    #echo in red color
    echo "$(tput setaf 1)$1$(tput sgr 0)"
}

#JDK:
if ! sudo apt-get install openjdk-7-jdk -y
then
    recho "ERROR: jdk installation failed. Aborting."
    exit 1
fi

#if ! grep -q "webupd8" /etc/apt/sources.list /etc/apt/sources.list.d/*; then
#    sudo add-apt-repository ppa:webupd8team/java -y
#    sudo apt-get update
#fi
#if ! sudo apt-get install oracle-java8-installer -y
#then
#    recho "ERROR: jdk 8 installation failed. Aborting."
#    exit 1
#fi
#if ! sudo apt-get install oracle-java8-set-default -y
#then
#    recho "ERROR: jdk 8 installation failed. Aborting."
#    exit 1
#fi

if ! grep 'JAVA_HOME' ~/.bashrc
then
    gecho "setting JAVA_HOME"
    echo "export JAVA_HOME=\"/usr/lib/jvm/java-7-openjdk-amd64\"" >> ~/.bashrc
fi
export JAVA_HOME="/usr/lib/jvm/java-7-openjdk-amd64"

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
        echo "export PATH=\"$HOME/anaconda2/bin:$PATH\" #anacondaPath" >> ~/.bashrc
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

#PyJnius
if ! python -c "import jnius"
then
    gecho "==== Installing pyjnius ===="
    pip install git+git://github.com/kivy/pyjnius.git
else
    gecho "pyjnius already installed."
fi

#chmod
chmod a+x ./bin/dump_json.py

#add to path
if ! grep 'butta' ~/.bashrc
then
    gecho "adding ./bin to .bashrc"
    echo "export PATH=\"`pwd`/bin:$PATH\" #buttaPath" >> ~/.bashrc
fi

gecho "INSTALLATION SUCCESSFUL!"


