#!/bin/bash


IPMOTG84="192.168.0.208"
PTOMOTG84=9055
PTOMETEG84=7777


meteespejo () {
  { echo "mete"; sleep 1; } | nc $IPMOTG84 $PTOMETEG84
}

sacaespejo () {
  { echo "saca"; sleep 1; } | nc $IPMOTG84 $PTOMETEG84
}

initespejo () {
  { echo "init"; sleep 1; } | nc $IPMOTG84 $PTOMETEG84
}

edoespejo () {
  { echo "estado"; sleep 1; } | nc $IPMOTG84 $PTOMETEG84
}

ejear () {
  { echo "EJEAR $@  FCMD"; sleep 1; } | nc $IPMOTG84 $PTOMOTG84
}

ejedec () {
  { echo "EJEDEC $@  FCMD"; sleep 1; } | nc $IPMOTG84 $PTOMOTG84
}

ejefoco () {
  { echo "EJEFOCO $@  FCMD"; sleep 1; } | nc $IPMOTG84 $PTOMOTG84
}

cierra_lazos_g84 () {
  ejear CONTROL_PIDX
  ejefoco CONTROL_PIDX
  ejedec CONTROL_PIDX
}

abre_lazos_g84 () {
  ejear DAX 0
  ejefoco DAX 0
  ejedec DAX 0
}

edog84 () {
  { echo "EG? EGJ"; sleep 1; } | nc $IPMOTG84 $PTOMOTG84
}

edog84j () {
  { echo "EGJ"; sleep 1; } | nc $IPMOTG84 $PTOMOTG84 | tr "," "\n"
}

ag84 () {
  { echo "$@"; sleep 1; } | nc $IPMOTG84 $PTOMOTG84
}

