#!/bin/bash

# Colores
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # Sin color

# Diccionario de IPs (mismo puerto para todos excepto ESPEJO)
declare -A EJE_IPS=(
  ["FOCO"]="192.168.8.2"
  ["DEC"]="192.168.9.2"
  ["AR"]="192.168.10.2"
  ["ESPEJO"]="127.0.0.1"
)

PORT=9095
PORT_ESPEJO=7777

# Orden explícito de los ejes
EJES=("FOCO" "DEC" "AR" "ESPEJO")

while true; do
    clear
    echo -e "${CYAN}====== ESTADO DE LOS BEAGLEBONES ======${NC}"
    DATE=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "🕒 $DATE"

    for EJE in "${EJES[@]}"; do
        IP=${EJE_IPS[$EJE]}

        if [ "$EJE" == "ESPEJO" ]; then
            PORT_USAR=$PORT_ESPEJO
        else
            PORT_USAR=$PORT
        fi

        echo -e "\n🔧 ${CYAN}$EJE ($IP:$PORT_USAR)${NC}"

        RESPONSE=$(echo ESTADO | nc -w 1 "$IP" "$PORT_USAR" 2>/dev/null)

        if [ $? -eq 0 ] && [ -n "$RESPONSE" ]; then
            echo -e "${GREEN}$RESPONSE${NC}"
        else
            echo -e "${RED}(Sin respuesta o fallo de conexión)${NC}"
        fi
    done

    sleep 1
done
