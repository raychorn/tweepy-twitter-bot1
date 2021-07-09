#!/bin/bash

VENV=.venv
REQS=./requirements.txt

TARGET_PY="3.9"
LOCAL_BIN=~/.local/bin

DIR0="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

PWD=$(pwd)
CURRENT_VENV=$(ls $PWD/$VENV*/bin/activate)
echo "PWD:$PWD, CURRENT_VIEW=$CURRENT_VENV"

if [ -f $CURRENT_VENV ]; then
    source $CURRENT_VENV
fi
py_vers=$(python -c 'import sys; i=sys.version_info; print("{}.{}.{}".format(i.major,i.minor,i.micro))')
echo "py_vers:$py_vers"

python39=$(which python3.9)

ARRAY=()

find_python(){
    echo "$1"
    PYTHONS=$(whereis $1)
    for val in $PYTHONS; do
        if [[ $val == *"/usr/bin/"* ]]; then
            if [[ $val != *"-config"* ]]; then
                ARRAY+=($val)
            fi
        fi
    done
}

find_python python
find_python pypy3

ur_good=0

v=$($python39 sort.py "${ARRAY[@]}")
ARRAY=()
ARRAY2=()
for val in $v; do
    ARRAY+=($val)
    x=$($val -c 'import sys; i=sys.version_info; print("{}.{}.{}".format(i.major,i.minor,i.micro))')
    if [[ $x == $py_vers ]]; then
        ur_good=1
        x="$x <-- $CURRENT_VENV"
    fi
    ARRAY2+=("$val $x")
done

if [ $ur_good == 0 ]; then
    PS3="Choose: "

    select option in "${ARRAY2[@]}";
    do
        echo "Selected number: $REPLY"
        choice=${ARRAY[$REPLY-1]}
        break
    done
else
    echo "Your current .venv ($CURRENT_VENV) is current."
    choice="python"
fi

version=$($choice --version)
echo "Use this -> $choice --> $version"
