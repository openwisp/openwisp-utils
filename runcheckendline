#!/bin/bash
flag=0
for i in $(find . -type f ! -path "*/*.egg-info/*"\
    ! -path "./.*"\
    ! -path "*.min.*"\
    ! -path "*.svg" -exec grep -Iq . {} \; -and -print); do
    if [ "$(tail -c 1 $i)" != "" ]; then
        echo "$i needs newline at the end"
        flag=1
    fi
done
exit $flag
