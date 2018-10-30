#!/bin/sh
for dir in *
do
    if [ -d $dir ]
    then
        echo $dir
        rm -rf $dir/*.pyc
    fi
done
rm -rf ./*.pyc
