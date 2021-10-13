#! /bin/bash

if [ "$#" -eq 1 ]; then
    echo -n "Sending Message to: "
    echo $1
    echo -n "@ Current Time: $(date +%H:%M:%S)" > $1
else
    echo "Please enter your fifo filename."
fi
