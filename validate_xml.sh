#!/usr/bin/env bash

ko_files=0
ok_files=0
total_files=0

if [ $# -eq 2 ]
then
    for xmlfile in $2/*.xml
    do
        let "total_files=total_files+1"
        xmllint --schema $1 $xmlfile --noout 
        if [ $? -eq 0 ]
        then
            let "ok_files=ok_files+1"
        else
            let "ko_files=ko_files+1"
        fi
    done

    echo "Total $total_files : OK=$ok_files / KO=$ko_files"

else
    echo "$0 <xsd file> <xml directory>"
fi
