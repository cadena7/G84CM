#!/bin/bash

bash config_ips_g84.sh

sleep 1


#bash checa_ping.sh

echo "al dir de python"
cd ..

#python servg84_edgar_v2.py &> /dev/null &
#python servg84_edgar_v2.py > /dev/null &
sleep 1



#source /home/guiador/venv/bin/activate
#python g84drvmqtt_edgar.py &> /dev/null &
#python g84drvmqtt.py &> /dev/null &
#python g84drvmqtt.py &> /dev/shm/g84drv.log &

echo "Fin $0" 
