#!/bin/bash

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/games:/usr/games


id1=2215SPB01978
id2=2215SPB01132
id3=2208SPB03042



ip1=192.168.8
ip2=192.168.9
ip3=192.168.10



function conf_ip () {
 IP=$3
 DEV=$2
 SERID=$1

 echo "IP=" $IP
 echo "DEV=" $DEV 
 echo "SERID=" $SERID
 sudo ifconfig $DEV ${IP}.1
 sudo route add -host ${IP}.2  gw ${IP}.1 ${DEV}
}



for i in {0..2};
do
 devid=eth$(($i+1))
 echo ${devid}
 res=$(udevadm info  /sys/class/net/${devid}|grep ID_USB_SERIAL_SHORT)
 echo "res=" $res
 id=$(echo ${res} | tr '=' ' '| awk '{print $3}' )

 [ "${id}"  == "${id1}" ] && conf_ip $id1 ${devid} ${ip1}

 [ "${id}"  == "${id2}" ] && conf_ip $id2 ${devid} ${ip2}

 [ "${id}"  == "${id3}" ] && conf_ip $id3 ${devid} ${ip3}

done
