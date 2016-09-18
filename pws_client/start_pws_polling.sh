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

    script_launch_cmd="python3 $PWS_CLIENT_PROJECT_PATH/fetch_widget_data.py"
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

while true ; do
    if kill -0 $poll_script_pid ; then
        sleep 5
    else
        logFn "polling script exited - try to restart it"
        startPollingScript
    fi
done
    
    

exit 0
