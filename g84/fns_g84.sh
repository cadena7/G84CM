#!/bin/bash


IPMOTG84="192.168.0.208"
PTOMOTG84=9055
PTOMETEG84=7777


meteespejo () {
  echo "mete" | nc -q0 $IPMOTG84 $PTOMETEG84
}

sacaespejo () {
  echo "saca" | nc -q0 $IPMOTG84 $PTOMETEG84
}

initespejo () {
  echo "init" | nc -q0 $IPMOTG84 $PTOMETEG84
}

edoespejo () {
  echo "estado" | nc -q0 $IPMOTG84 $PTOMETEG84
}

ejear () {
 echo "EJEAR $@  FCMD" | nc -q0 $IPMOTG84 $PTOMOTG84
}

ejedec () {
 echo "EJEDEC $@  FCMD" | nc -q0 $IPMOTG84 $PTOMOTG84
}

ejefoco () {
 echo "EJEFOCO $@  FCMD" | nc -q0 $IPMOTG84 $PTOMOTG84
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
  echo "EG? EGJ" | nc -q0 $IPMOTG84 $PTOMOTG84
}

edog84j () {
echo "EGJ" | nc -q0 $IPMOTG84 $PTOMOTG84 | tr  "," "\n"
    }

ag84 () {
   echo "$@" | nc -q0 $IPMOTG84 $PTOMOTG84
}
