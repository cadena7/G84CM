#! /bin/bash

# Script p. ejec. los programas de control del guiador 84cm
# 2025
# E.O.C.Z. 29 septiembre, 2025

## Ejecuta las ventanas

# afranco - grulla lab setup
cd /home/observa/cadena/guiador/g84
./kill-g84-gscui.sh
sleep 2

cd /home/observa/cadena/guiador/test_epl/epls/scripts
./ejec_gsc_d.sh stop
./ejec_consola_d.sh stop
sleep 1
./corre_serv_gsc_84.sh

cd /home/observa/cadena/guiador/test_epl/uiepls/scripts
./ejec_gscui.sh > /dev/null &
sleep 1
./ejec_mot_guiadorui-84.sh > /dev/null &
sleep 1




. $HOME/instrumentacion/pon_amb_84.sh
export INSTRUMENTACION=$HOME/instrumentacion
export LD_LIBRARY_PATH=$INSTRUMENTACION/lib/

rm -r -f /tmp/gsc-tmp
mkdir -p /tmp/gsc-tmp
rm /tmp/gsc-gtk.sock
rm /tmp/autoguiado.log


ELFAUCET=$INSTRUMENTACION/bin/g84-faucet

#killall -KILL $ELFAUCET
killall -KILL $ELFAUCET


$ELFAUCET 4957 --in --out /bin/bash $INSTRUMENTACION/bin/trad-guiado.sh &

