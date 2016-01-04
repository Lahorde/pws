#!/bin/bash

export PWS_CLIENT_PROJECT_PATH=`dirname $0`
source $PWS_CLIENT_PROJECT_PATH/../pws_params.sh

function logFn {
    echo `date +'%F %R %S'` - `basename $0` - $1
}

function startPollingScript {
    # Wait for connection to be ready
    while ! ping -c 1 google.fr > /dev/null 2>&1
    do
        logFn "no connection up"
        sleep 2
    done
    logFn "connection up"

    script_launch_cmd="python2 $PWS_CLIENT_PROJECT_PATH/wu_pws_polling.py start"
    eval $script_launch_cmd
    
    if [ $? -eq 0 ]
    then
        poll_script_pid=$(pgrep -f "$script_launch_cmd" )
        logFn "wu polling script started - pid = $poll_script_pid"
    else
        logFn "Error $? when launching python2 $PWS_CLIENT_PROJECT_PATH/wu_pws_polling.py start - exiting"
        exit 1
    fi
}

logFn "start pws display"

startPollingScript

#for reactivity at startup
counter=0
while ! find $PWS_POLLING_DATA_PATH > /dev/null 2>&1 
do
    logFn "wu polling data not created"
    if [ $counter -gt 10 ]
    then
        sleep 10
    else
        sleep 2
        (( counter++ ))
    fi
done

counter=0
while [ $(expr $(date +%s) - $(date +%s -r $PWS_POLLING_DATA_PATH)) -gt 300 ]
do
    logFn "$PWS_POLLING_DATA_PATH not updated"
    if [ $counter -gt 10 ]
    then
        sleep 10
    else
        sleep 2
        (( counter++ ))
    fi
done


while true ; do
    if kill -0 $poll_script_pid ; then
        sleep 5
    else
        logFn "polling script exited - try to restart it"
        startPollingScript
    fi
done
    
    

exit 0