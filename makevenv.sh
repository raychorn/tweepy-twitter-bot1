#!/bin/bash

VENV=.venv
REQS=./requirements.txt

LOCAL_BIN=~/.local/bin

DIR0="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

ARRAY=()

find_python(){
    pythons=$1
    PYTHONS=$(whereis $pythons)
    for val in $PYTHONS; do
        if [[ $val == *"/usr/bin/"* ]]; then
            if [[ $val != *"-config"* ]]; then
                ARRAY+=($val)
            fi
        fi
    done
}

python39=$(which python3.9)

if [[ -f $python39 ]]
then
    echo "Found $python39"
else
    echo "Installing python3.9"
    apt update -y
    apt install software-properties-common -y
    echo -ne '\n' | add-apt-repository ppa:deadsnakes/ppa
    apt install python3.9 -y
	apt install python3.9-distutils -y
fi

python39=$(which python3.9)
pip3=.

if [[ -f $python39 ]]
then
    pip_local=$LOCAL_BIN/pip3
    if [[ -f $pip_local ]]
    then
        echo "Found $pip_local"
        export PATH=$LOCAL_BIN:$PATH
    else
        GETPIP=$DIR0/get-pip.py

        if [[ -f $GETPIP ]]
        then
            $python39 $GETPIP
            export PATH=$LOCAL_BIN:$PATH
            pip3=$(which pip3)
            if [[ -f $pip3 ]]
            then
                $pip3 install --upgrade setuptools
            fi
        fi

        if [[ -f $pip3 ]]
        then
            $pip3 install --upgrade setuptools
            $pip3 install --upgrade pip
        fi
    fi
fi

pip3=$(which pip3)
echo "pip3 is $pip3"

if [[ -f $pip3 ]]
then
    $pip3 install --upgrade setuptools
    $pip3 install virtualenv
    $pip3 install --upgrade virtualenv
fi

find_python python

pyston="/usr/bin/pyston3.8"

if [[ -f $pyston ]]
then
    echo "Found $pyston"
else
    apt-get install wget -y
    wget https://github.com/pyston/pyston/releases/download/v2.1/pyston_2.1_20.04.deb

    pyston_deb="$DIR0/pyston_2.1_20.04.deb"
    if [[ -f $pyston_deb ]]
    then
        apt install $pyston_deb -y
        rm -f $pyston_deb
    fi
fi

find_python pyston

echo ${ARRAY[@]}
v=$($python39 sort.py "${ARRAY[@]}")
echo "Use this -> $v"
ARRAY=()
ARRAY2=()
for val in $v; do
    ARRAY+=($val)
    x=$($val -c 'import sys; i=sys.version_info; print("{}.{}.{}".format(i.major,i.minor,i.micro))')
    ARRAY2+=("$val $x")
done
echo ${ARRAY[@]}
echo ${ARRAY2[@]}

PS3="Choose: "

select option in "${ARRAY2[@]}";
do
    echo "Selected number: $REPLY"
    choice=${ARRAY[$REPLY-1]}
    break
done

version=$($choice --version)
echo "Use this -> $choice --> $version"

v=$($choice -c 'import sys; i=sys.version_info; print("{}{}{}".format(i.major,i.minor,i.micro))')
echo "Use this -> $choice --> $v"

VENV=$VENV$v
echo "VENV -> $VENV"

if [[ -d $VENV ]]
then
    rm -R -f $VENV
fi

if [[ ! -d $VENV ]]
then
    virtualenv --python $choice -v $VENV
fi

if [[ -d $VENV ]]
then
    . ./$VENV/bin/activate
    pip install --upgrade setuptools
    pip install --upgrade pip

    if [[ -f $REQS ]]
    then
        pip install -r $REQS
    fi

fi