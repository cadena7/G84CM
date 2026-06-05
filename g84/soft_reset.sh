#!/bin/bash
#sudo apt install sshpass

sshpass -p "p4guiador" ssh -o StrictHostKeyChecking=no guiador@192.168.0.208 "
  sh /home/guiador/dist/scripts/aplica.sh ;
  sudo supervisorctl reload
"