#!/bin/bash

export PWS_CLIENT_PROJECT_PATH=`dirname $0`

#wait here to have conky over background
if conky -d -c $PWS_CLIENT_PROJECT_PATH/conky/conkyrc_pws_obs
then
    echo "PWS widget successfully displayed"
else
    echo "Unable to display PWS widget - Error $?"
    exit 1
fi

exit 0