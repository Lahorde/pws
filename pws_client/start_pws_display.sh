#!/bin/bash

export PWS_CLIENT_PROJECT_PATH=`dirname $0`
source $PWS_CLIENT_PROJECT_PATH/../pws_params.sh

function logFn {
    echo `date +'%F %R %S'` - `basename $0` - $1
}

logFn "start pws display"

# Wait for connection to be ready
while ! ping -c 1 google.fr > /dev/null 2>&1
do
    logFn "no connection up"
    sleep 2
done
logFn "connection up"

if python2 $PWS_CLIENT_PROJECT_PATH/wu_pws_polling.py start 
then
    logFn "wu polling script started"
else
    logFn "Error $? when launching python2 $PWS_CLIENT_PROJECT_PATH/wu_pws_polling.py start - exiting"
    exit 1
fi

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

#wait here to have conky over background
sleep 2
logFn "launch conky display"

if conky -d -c $PWS_CLIENT_PROJECT_PATH/conky/conkyrc_pws_obs
then
    logFn "PWS widget successfully displayed"
else
    logFn "Unable to display PWS widget - Error $?"
    exit 1
fi

exit 0