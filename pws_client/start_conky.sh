#!/bin/bash
export PWS_CLIENT_PROJECT_PATH=`dirname $0`
source $PWS_CLIENT_PROJECT_PATH/../pws_params.sh

#for reactivity at startup
counter=0
while ! find $PWS_POLLING_DATA_PATH > /dev/null 2>&1 
do
    echo "wu polling data not created"
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
    echo "$PWS_POLLING_DATA_PATH not updated"
    if [ $counter -gt 10 ]
    then
        sleep 10
    else
        sleep 2
        (( counter++ ))
    fi
done

#wait here to have conky over background
if conky -d -c $PWS_CLIENT_PROJECT_PATH/conky/conkyrc_pws_obs
then
    echo "PWS widget successfully displayed"
else
    echo "Unable to display PWS widget - Error $?"
    exit 1
fi

exit 0