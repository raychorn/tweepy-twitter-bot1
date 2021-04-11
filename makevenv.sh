#!/bin/bash

VENV=.venv
REQS=./requirements.txt

LOCAL_BIN=~/.local/bin

DIR0="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

ARRAY=()

qsort() {
    local pivot i smaller=() larger=()
    qsort_ret=()
    (($#==0)) && return 0
    pivot=$1
    shift
    for i; do
        # This sorts strings lexicographically.
        if [[ $i < $pivot ]]; then
            smaller+=( "$i" )
        else
            larger+=( "$i" )
        fi
    done
    qsort "${smaller[@]}"
    smaller=( "${qsort_ret[@]}" )
    qsort "${larger[@]}"
    larger=( "${qsort_ret[@]}" )
    qsort_ret=( "${smaller[@]}" "$pivot" "${larger[@]}" )
}

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
pip3=.

if [[ -f $python39 ]]
then
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

pip3=$(which pip3)

if [[ -f $pip3 ]]
then
    $pip3 install --upgrade setuptools
fi

find_python python

apt-get install wget -y
wget https://github.com/pyston/pyston/releases/download/v2.1/pyston_2.1_20.04.deb

pyston_deb="$DIR0/pyston_2.1_20.04.deb"
if [[ -f $pyston_deb ]]
then
    apt install $pyston_deb -y
    rm -f $pyston_deb
fi

find_python pyston

qsort "${ARRAY[@]}"

PS3="Choose: "

select option in "${ARRAY[@]}";
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