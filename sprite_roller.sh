#!/bin/bash

TM=`./sr_roller.py -q $1`
SPRITE=`./sr_roller.py -q $2`
SOAK=`./sr_roller.py -q $3`
let "NET_TM=$TM-$SPRITE"
let "NET_SOAK=$SPRITE*2-$SOAK"

if [ $NET_TM -lt 0 ]
then
    NET_TM=0
fi
if [ $NET_SOAK -lt 0 ]
then
    NET_SOAK=0
fi
echo "Tasks: $NET_TM"
echo "Damage: $NET_SOAK"

