#!/bin/bash  

serverInterface=$1
peerPublicKey=$2

/usr/bin/wg set $serverInterface peer $peerPublicKey remove