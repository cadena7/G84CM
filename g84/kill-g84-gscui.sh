#! /bin/bash

# Manual script to kill orphan processes left by nuevo-guiador-test-2024.sh
# This is only a temporal script while the final solution is implemented

# afranco - grulla lab setup
for pid in $(ps -ef | grep "python gscui.py --port 1883 --host 192.168.0.239 --debug=1 --tel=84cm" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "/bin/bash ./ejec_gscui.sh" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "python -m consolad.consolad --host_mqtt 192.168.0.239 --port_mqtt 1883 --host 192.168.0.10 --port 4955 --latitud=31.045277778 --longitud=-115.46666667 --telescopio=84cm" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "python motgui-84.py --port 1883 --host 192.168.0.239 --debug=2" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "/bin/bash ./ejec_mot_guiadorui-84.sh" | awk '{print $2}'); do kill -15 $pid; done

#for pid in $(ps -ef | grep "/home/observa/instrumentacion/bin/camguiador -p4950 -h192.168.0.206 -i0" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "python gscui.py" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "python motgui-84.py" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "/home/observa/instrumentacion/bin/g84-faucet 4957 --in --out /bin/bash /home/observa/instrumentacion/bin/trad-guiado.sh" | awk '{print $2}'); do kill -15 $pid; done

for pid in $(ps -ef | grep "python gscd.py --host 192.168.0.239 --port 1883 --tel 84cm" | awk '{print $2}'); do kill -15 $pid; done


