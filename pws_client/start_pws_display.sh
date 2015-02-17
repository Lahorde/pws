#!/bin/bash

export PWS_CLIENT_PROJECT_PATH=`dirname $0`
source $PWS_CLIENT_PROJECT_PATH/../pws_params.sh

echo start pws display

# Wait for connection to be ready
while ! ping -c 1 google.fr > /dev/null 2>&1
do
    echo no connection up
    sleep 2
done
echo connection up

if python2 $PWS_CLIENT_PROJECT_PATH/wu_pws_polling.py start
then
    echo  wu polling script started
else
    echo Error $? when launching python2 $PWS_CLIENT_PROJECT_PATH/wu_pws_polling.py start - exiting
    exit 1
fi

#for reactivity at startup
counter=0
while ! find $PWS_POLLING_DATA_PATH > /dev/null 2>&1 
do
    echo wu polling data not created
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
    echo $PWS_POLLING_DATA_PATH not updated
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
echo launch conky display
conky -d -c $PWS_CLIENT_PROJECT_PATH/conky/conkyrc_pws_obs

exit 0