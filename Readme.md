# Guiador del telescopio de 84 cm

Software de control, operacion, monitoreo y diagnostico del guiador del
telescopio de 84 cm. El sistema controla los ejes **AR**, **DEC** y **FOCO**,
el mecanismo del **espejo**, publica estado por MQTT y ofrece interfaces
graficas para operacion.

> **ADVERTENCIA DE SEGURIDAD**
>
> Este repositorio controla hardware real. Los comandos `DAX`, movimientos
> absolutos/relativos, busquedas de centro, inicializacion de ejes y movimiento
> del espejo pueden producir movimiento fisico inmediato. Antes de ejecutarlos:
>
> - Confirme visualmente que el mecanismo puede moverse sin obstrucciones.
> - Verifique limites, switches, sentido de movimiento y comunicacion.
> - Mantenga disponible una forma de detener el movimiento.
> - No deje un eje en lazo abierto ni con `DAX` distinto de cero.

## Contenido

- [Arquitectura](#arquitectura)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Mapa de red y puertos](#mapa-de-red-y-puertos)
- [Instalacion y dependencias](#instalacion-y-dependencias)
- [Arranque y parada](#arranque-y-parada)
- [MQTT](#mqtt)
- [Comandos TCP y sockets](#comandos-tcp-y-sockets)
- [Operacion de ejes](#operacion-de-ejes)
- [Entonacion PID](#entonacion-pid)
- [Limites mecanicos y ceros](#limites-mecanicos-y-ceros)
- [PocketBeagles](#pocketbeagles)
- [Espejo](#espejo)
- [Logger MQTT](#logger-mqtt)
- [Diagnostico y recuperacion](#diagnostico-y-recuperacion)
- [Despliegue y configuracion](#despliegue-y-configuracion)
- [Archivos importantes](#archivos-importantes)

## Arquitectura

Flujo principal actual:

```text
UI motores / clientes MQTT
          |
          v
Broker MQTT 192.168.0.239:1883
          |
          v
rpi/dist/g84drvmqtt_edgar.py
          |
          v
TCP local/RPi :9055 -> servg84_edgar_v2.py -> instruccionesguiador.py
          |
          +----------+----------+
          |          |          |
          v          v          v
   FOCO .8.2    DEC .9.2    AR .10.2
       :9095        :9095       :9095
```

Servicios principales de la Raspberry Pi:

- `servg84`: servidor TCP de comandos del guiador en puerto `9055`.
- `mqtt`: puente MQTT hacia el servidor TCP local.
- `espejo`: servidor TCP del espejo en puerto `7777`.
- `espejo_mqtt`: puente MQTT para el espejo.
- `reinicio_automatico`: servicio auxiliar de recuperacion.

Existe ademas un backend EPL historico/alternativo bajo `test_epl/epls/`. El
backend actual de la Raspberry Pi y el backend EPL no deben confundirse:

- Backend actual de la Pi: TCP `9055`, MQTT directo y PocketBeagles.
- Backend EPL legado: `motorsguiad.py`, configurado en scripts con
  `192.168.0.131:2525`.

## Estructura del repositorio

| Ruta | Descripcion |
| --- | --- |
| `g84/` | Scripts de operacion, recuperacion, movimiento y entonacion |
| `g84/G84_Logger/` | Captura de estado MQTT a SQLite, Excel y graficas |
| `rpi/dist/` | Backend principal instalado en la Raspberry Pi |
| `rpi/Espejo/` | Control TCP y MQTT del espejo |
| `rpi/config/` | Limites mecanicos y offsets de cero |
| `rpi/supervisor/` | Configuracion de servicios Supervisor |
| `pocketbb/` | Software y utilidades para PocketBeagle |
| `test_epl/epls/` | Servicios backend EPL-MQTT |
| `test_epl/uiepls/` | Interfaces graficas EPL-MQTT |
| `test_epl/tests/` | Pruebas unitarias actuales |
| `limites_mecanicos_G84.txt` | Registro historico de limites medidos |

## Mapa de red y puertos

### Direcciones principales

| Equipo/servicio | IP o host | Puerto | Protocolo/uso |
| --- | --- | --- | --- |
| Broker MQTT 84 cm | `192.168.0.239` | `1883` | MQTT |
| Raspberry Pi guiador | `192.168.0.208` | `9055` | TCP de comandos |
| Espejo en Raspberry Pi | `192.168.0.208` / `localhost` | `7777` | TCP |
| PocketBeagle FOCO | `192.168.8.2` | `9095` | TCP servo |
| PocketBeagle DEC | `192.168.9.2` | `9095` | TCP servo |
| PocketBeagle AR | `192.168.10.2` | `9095` | TCP servo |
| PocketBeagle ZOOM, referencia historica | `192.168.7.2` | `9095` | TCP servo |
| SSH PocketBeagles | IP de cada PocketBeagle | `2276` | SSH |
| Supervisor HTTP/XML-RPC | Raspberry Pi | `9001` | Supervisor |

## Instalacion y dependencias

El repositorio incluye entornos virtuales historicos (`venv3/` y `rpi/venv/`),
pero para una instalacion limpia se recomienda crear uno nuevo:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Dependencias usadas por los componentes principales:

```bash
python -m pip install aiomqtt paho-mqtt simplejson
python -m pip install pandas openpyxl matplotlib seaborn
```

Las interfaces graficas requieren GTK/PyGObject y `endpointlib`, normalmente
instalados en el ambiente de operacion del observatorio. El control del espejo
requiere ademas Raspberry Pi GPIO y la biblioteca Adafruit Motor HAT.

Herramientas de sistema usadas por los scripts:

```bash
sudo apt install netcat-openbsd mosquitto-clients supervisor sshpass
```

En macOS, `nc` no acepta `-q0`; use `g84/fns_g84_mac.sh`.

## Arranque y parada

### Operacion habitual desde la computadora de observacion

El script principal abre los servicios GSC/consola y las interfaces del
guiador:

```bash
cd g84
./nuevo-guiador-2025.sh
```

Las rutas internas de este script estan fijadas para
`/home/observa/cadena/guiador`; deben ajustarse si cambia la instalacion.

### Servicios EPL

```bash
cd test_epl/epls/scripts
source config_lugar.sh
./arranca_servs_epls.sh
```

Arranque/parada individual:

```bash
EPLS_CONF_DIR="$PWD" ./ejec_gsc_d.sh start
EPLS_CONF_DIR="$PWD" ./ejec_gsc_d.sh stop

EPLS_CONF_DIR="$PWD" ./ejec_consola_d.sh start
EPLS_CONF_DIR="$PWD" ./ejec_consola_d.sh stop
```

### Interfaces graficas

```bash
cd test_epl/uiepls/scripts
./ejec_gscui.sh
./ejec_mot_guiadorui-84.sh
```

Ejecucion directa de la UI de motores:

```bash
cd test_epl/uiepls/motoresui/src
python motgui-84.py --host 192.168.0.239 --port 1883 --debug=2
```

### Supervisor en la Raspberry Pi

```bash
sudo supervisorctl status
sudo supervisorctl restart servg84
sudo supervisorctl restart mqtt
sudo supervisorctl restart espejo
sudo supervisorctl restart espejo_mqtt
sudo supervisorctl reload
```

La configuracion versionada esta en `rpi/supervisor/guiador_services.conf`.

## MQTT

Broker configurado actualmente:

```text
Host: 192.168.0.239
Puerto: 1883
```

Monitorear todos los topicos del guiador:

```bash
mosquitto_sub -h 192.168.0.239 -t 'oan/control/84cm/guiador/#' -v
```

### Topicos de motores

Prefijo: `oan/control/84cm/guiador/motores/`

| Topico | Direccion | Payload/funcion |
| --- | --- | --- |
| `mueve` | entrada | JSON con posiciones absolutas |
| `mueve_relativo` | entrada | JSON con incrementos |
| `dame_estado` | entrada | Solicita publicacion inmediata |
| `inicializa_ejes` | entrada | JSON con ejes a buscar/inicializar |
| `define_coordenadas` | entrada | Define cero; solo se acepta valor `0` |
| `cambia_params` | entrada | Cambia parametros/control |
| `status` | salida | Estado, posiciones, limites y offsets |
| `config` | salida retained | Configuracion autoritaria de limites y offsets |
| `comando` | salida/legado | Mensajes hacia UI EPL |

Ejemplos seguros de consulta:

```bash
mosquitto_sub -h 192.168.0.239 \
  -t 'oan/control/84cm/guiador/motores/status' -v

mosquitto_sub -h 192.168.0.239 \
  -t 'oan/control/84cm/guiador/motores/config' -v

mosquitto_pub -h 192.168.0.239 \
  -t 'oan/control/84cm/guiador/motores/dame_estado' -m '{}'
```

Ejemplos que producen movimiento:

```bash
# Movimiento absoluto: AR/DEC en arcsec, FOCO en mm
mosquitto_pub -h 192.168.0.239 \
  -t 'oan/control/84cm/guiador/motores/mueve' \
  -m '{"AR": 100.0, "DEC": 50.0, "FOCO": 2.0}'

# Movimiento relativo
mosquitto_pub -h 192.168.0.239 \
  -t 'oan/control/84cm/guiador/motores/mueve_relativo' \
  -m '{"AR": 5.0}'

# Inicializar un eje
mosquitto_pub -h 192.168.0.239 \
  -t 'oan/control/84cm/guiador/motores/inicializa_ejes' \
  -m '{"DEC": 1}'

# Definir la posicion actual como cero de usuario
mosquitto_pub -h 192.168.0.239 \
  -t 'oan/control/84cm/guiador/motores/define_coordenadas' \
  -m '{"AR": 0}'
```

Los movimientos absolutos y relativos son limitados por
`rpi/dist/g84drvmqtt_edgar.py`. Un movimiento relativo se rechaza si no existe
una posicion reciente, actualmente con timeout de `5 s`.

### Topicos del espejo

Prefijo: `oan/control/84cm/guiador/espejo/`

| Topico | Uso |
| --- | --- |
| `control` | Recibe `INIT`, `ESTADO`, `METE`, `SACA`, `STOP` |
| `estado` | Publica JSON retained con el estado del espejo |

```bash
mosquitto_sub -h 192.168.0.239 \
  -t 'oan/control/84cm/guiador/espejo/#' -v

mosquitto_pub -h 192.168.0.239 \
  -t 'oan/control/84cm/guiador/espejo/control' -m ESTADO
```

### Topicos GSC

Prefijo: `oan/control/84cm/gsc/`

- Entradas: `params_gsc`, `actualiza_coordenadas`, `buscar`.
- Salidas: `lista_objetos`, `status`.
- El GSC tambien escucha `oan/control/84cm/consola/mueve` y
  `oan/control/84cm/consola/status`.

## Comandos TCP y sockets

### Servidor principal del guiador: puerto 9055

Cargar funciones de conveniencia:

```bash
source g84/fns_g84.sh       # Linux
source g84/fns_g84_mac.sh   # macOS
```

Funciones disponibles:

| Funcion | Uso |
| --- | --- |
| `edog84j` | Estado JSON formateado |
| `edog84` | Estado general |
| `ejear ...` | Envia comando directo a AR |
| `ejedec ...` | Envia comando directo a DEC |
| `ejefoco ...` | Envia comando directo a FOCO |
| `ag84 ...` | Envia comando crudo al servidor `9055` |
| `abre_lazos_g84` | Pone `DAX 0` en los tres ejes |
| `cierra_lazos_g84` | Activa `CONTROL_PIDX` en los tres ejes |
| `meteespejo`, `sacaespejo`, `initespejo`, `edoespejo` | Control del espejo |

Consultas directas:

```bash
echo 'EGJ' | nc -q0 192.168.0.208 9055
echo 'EG? EGJ' | nc -q0 192.168.0.208 9055
```

Comandos reconocidos por el interprete principal incluyen:

```text
AR= DEC= FOCO=
AR+ AR- DEC+ DEC- FOC+ FOC-
EG? EGJ EG+
ESC_PLACA=
EJEAR ... FCMD
EJEDEC ... FCMD
EJEFOCO ... FCMD
BUSCA_CENTRO_AR BUSCA_CENTRO_DEC BUSCA_CENTRO_FOCO
CANCELA_INICIO_AR CANCELA_INICIO_DEC CANCELA_INICIO_FOCO
DEF_CERO_AR DEF_CERO_DEC DEF_CERO_FOCO
RESTABLECE_BANDERA_ERR
VEL_NORMAL_* VEL_CENTRADO_*
LEECFG
```

### Sockets directos de PocketBeagle: puerto 9095

```bash
echo ESTADO | nc -q0 192.168.8.2 9095   # FOCO
echo ESTADO | nc -q0 192.168.9.2 9095   # DEC
echo ESTADO | nc -q0 192.168.10.2 9095  # AR
```

Monitoreo continuo:

```bash
while sleep 1; do echo ESTADO | nc -q0 192.168.9.2 9095; done
```

### Socket del espejo: puerto 7777

```bash
echo ESTADO | nc -q0 192.168.0.208 7777
echo INIT   | nc -q0 192.168.0.208 7777
echo METE   | nc -q0 192.168.0.208 7777
echo SACA   | nc -q0 192.168.0.208 7777
echo STOP   | nc -q0 192.168.0.208 7777
```

## Operacion de ejes

### Consultar estado

```bash
source g84/fns_g84.sh
edog84j
```

### Abrir y cerrar lazos

```bash
# Abrir lazos / salida cero
abre_lazos_g84

# Cerrar lazos PID
cierra_lazos_g84
```

Equivalente por eje:

```bash
ejedec DAX 0
ejedec CONTROL_PIDX
```

### Mover a posiciones fijas

```bash
ag84 DEC= 800 FCMD
ag84 AR= 500 FCMD
ag84 FOCO= 20 FCMD
```

### Buscar centros/inicios

```bash
ag84 RESTABLECE_BANDERA_ERR FCMD
ag84 BUSCA_CENTRO_FOCO FCMD
ag84 BUSCA_CENTRO_AR FCMD
ag84 BUSCA_CENTRO_DEC FCMD
```

### Movimiento manual en lazo abierto

Use solo durante diagnostico y detenga siempre con `DAX 0`:

```bash
ejedec RST_S ERROR_MAXX 0
ejedec DAX -5000
sleep 2
ejedec DAX 0
```

Los scripts `g84/mueve_ar.sh`, `g84/mueve_dec.sh` y `g84/mueve_foco.sh`
realizan una maniobra similar durante 7 segundos. No ejecutarlos sin
supervision fisica.

## Entonacion PID

La entonacion persistente usada por el backend se encuentra en:

```text
rpi/dist/guiador84.cfg
```

El archivo es cargado por `rpi/dist/instruccionesguiador.py`. Para releerlo sin
reiniciar:

```bash
source g84/fns_g84.sh
ag84 LEECFG
```

Valores versionados actuales:

| Eje | KPX | KIX | KDX | ILX | BITIX | VX | AX | CGANX | ERROR_MAXX |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| AR | 60 | 0.001 | 1 | 4000 | 8 | 5 | 0.01 | `3000 1` | 26000 |
| DEC | 70 | 0.001 | 1 | 4000 | 8 | 2 | 0.001 | `120 3` | 3000 |
| FOCO | 70 | 0.001 | 1 | 4000 | 8 | 5 | 0.01 | `3000 1` | 26000 |

Velocidades configuradas:

| Eje | Normal | Centrado |
| --- | ---: | ---: |
| AR | 5 | 3 |
| DEC | 2 | 1 |
| FOCO | 5 | 3 |

### Procedimiento recomendado de entonacion

La entonacion debe realizarse sobre **un solo eje a la vez**, comenzando con
movimientos pequenos y lejos de los limites mecanicos. Antes de iniciar,
confirme que los otros ejes esten detenidos y que sea posible observar
fisicamente el mecanismo.

Use dos terminales durante el procedimiento:

**Terminal 1: comandos de entonacion y movimiento**

```bash
cd g84
source fns_g84.sh
edog84j
```

**Terminal 2: retroalimentacion de las PocketBeagles**

Ejecute desde la Raspberry Pi o desde un equipo que tenga acceso directo a las
redes de las PocketBeagles:

```bash
bash rpi/estadopockets.sh
```

Este script actualiza continuamente el estado de FOCO, DEC y AR. Durante la
entonacion, observe especialmente las cuentas actuales y deseadas del
codificador del eje seleccionado, ademas de errores, switches y estado del
lazo. La posicion actual debe acercarse a la deseada de manera estable, sin
oscilacion sostenida, sobreimpulso excesivo ni crecimiento del error.

Tambien puede monitorearse solamente un eje:

```bash
while sleep 0.2; do echo ESTADO | nc -q0 192.168.9.2 9095; done   # DEC
while sleep 0.2; do echo ESTADO | nc -q0 192.168.10.2 9095; done  # AR
while sleep 0.2; do echo ESTADO | nc -q0 192.168.8.2 9095; done   # FOCO
```

Flujo recomendado:

1. Consulte el estado y confirme que el eje se encuentra lejos de sus limites.
2. Abra el lazo y deje la salida en cero.
3. Restablezca el eje y cargue parametros conservadores.
4. Cierre el lazo con `CONTROL_PIDX`.
5. Envie destinos pequenos en ambos sentidos.
6. Compare continuamente las cuentas actuales y deseadas en
   `estadopockets.sh`.
7. Ajuste un parametro a la vez y repita el movimiento.
8. Al terminar, mande `DAX 0` y guarde los valores aceptados en
   `rpi/dist/guiador84.cfg`.

Ejemplo de preparacion y entonacion interactiva de DEC:

```bash
# Abrir el lazo, detener la salida y restablecer el servo
ejedec DAX 0 HABTASK RST FCMD

# Cargar parametros iniciales conservadores
ejedec KPX 12 KIX 0.001 KDX 0.1 ILX 4000 FCMD
ejedec VX= 3 AX= 0.6 FCMD

# Cerrar el lazo
ejedec ERROR_MAXX 6000 CONTROL_PIDX FCMD
```

Para probar directamente posiciones deseadas en **cuentas del codificador**,
use `X=` sobre el eje que se esta entonando. Comience con desplazamientos
pequenos respecto a la posicion actual observada:

```bash
ejedec X= 500 FCMD
ejedec X= 0 FCMD
ejedec X= -500 FCMD

ejear X= 1000 FCMD
ejear X= 0 FCMD

ejefoco X= 1000 FCMD
ejefoco X= 0 FCMD
```

No asuma que `X= 0` es una posicion mecanicamente segura: confirme primero el
cero y las cuentas actuales en `estadopockets.sh`. Evite saltos grandes y
detenga la prueba si el eje se mueve en sentido incorrecto, no converge, activa
un switch o presenta oscilaciones.

Tambien puede enviar una posicion usando las unidades de usuario del guiador:

```bash
ag84 DEC= 100 FCMD
ag84 DEC= 0 FCMD

ag84 AR= 100 FCMD
ag84 AR= 0 FCMD

ag84 FOCO= 2 FCMD
ag84 FOCO= 0 FCMD
```

AR y DEC se expresan en arcsec; FOCO se expresa en mm. Estos comandos pasan por
las conversiones geometricas de `instruccionesguiador.py`, mientras que `X=`
actua directamente sobre las cuentas deseadas del servo.

Para cambiar parametros al vuelo durante las pruebas:

```bash
ejear KPX 8 KIX 0.001 KDX 0.1 ILX 400
ejear CGANX 5000 2
ejear AX= 0.025 VX= 2
```

Recomendaciones de ajuste:

- Aumente `KPX` gradualmente hasta obtener una respuesta firme, evitando
  oscilacion sostenida.
- Use `KDX` para amortiguar sobreimpulso u oscilaciones.
- Mantenga `KIX` pequeno y vigile acumulacion integral; `ILX` limita esa
  acumulacion.
- Ajuste `VX` y `AX` para limitar velocidad y aceleracion antes de buscar una
  respuesta mas agresiva.
- Cambie un parametro a la vez y registre el resultado junto con el destino,
  las cuentas observadas y el error.
- Pruebe movimientos positivos y negativos, primero pequenos y despues dentro
  de todo el rango operativo permitido.

Al finalizar cada prueba o ante comportamiento inesperado:

```bash
ejedec DAX 0
# Cambiar por ejear o ejefoco segun el eje bajo prueba.
```

Los valores al vuelo no sustituyen automaticamente el contenido persistente de
`guiador84.cfg`.

Parametros geometricos actuales en `instruccionesguiador.py`:

| Parametro | Valor |
| --- | ---: |
| `ESC_PLACA` | `18.25` arcsec/mm |
| `PPMMAR` | `2000.0` |
| `PPMMDEC` | `144.0` |
| `PPMMFOCO` | `-2000.0` |

Los signos de PPMM deben verificarse con una estrella: el sentido de los
offsets del telescopio y del guiador debe coincidir.

## Limites mecanicos y ceros

Configuracion autoritaria:

```text
rpi/config/limites-motores-guiador-g84.json
rpi/config/offsets-cero-mecanicos-g84.json
```

El driver instalado espera estos archivos en:

```text
/home/guiador/config/limites-motores-guiador-g84.json
/home/guiador/config/offsets-cero-mecanicos-g84.json
```

Limites de switches versionados:

| Eje | Switch minimo | Switch maximo | Margen | Rango operativo |
| --- | ---: | ---: | ---: | ---: |
| AR | -1512 arcsec | 1385 arcsec | 10 | -1502 a 1375 |
| DEC | -884 arcsec | 1050 arcsec | 10 | -874 a 1040 |
| FOCO | -65 mm | 48 mm | 3 | -62 a 45 |

Los offsets permiten redefinir el cero de usuario sin perder la referencia
mecanica usada para proteger limites. Al recibir confirmacion `OK_CENTRO_*`
despues de inicializar un eje, su offset vuelve a cero.

El topico MQTT `.../config` publica retained:

- Version y configuracion de limites.
- Limites de switches.
- Limites operativos derivados.
- Offsets de cero actuales.

## PocketBeagles

Correspondencia actual:

| Eje | IP | Puerto servo | SSH |
| --- | --- | ---: | ---: |
| FOCO | `192.168.8.2` | `9095` | `2276` |
| DEC | `192.168.9.2` | `9095` | `2276` |
| AR | `192.168.10.2` | `9095` | `2276` |

Conexion SSH:

```bash
ssh -p 2276 debian@192.168.8.2
ssh -p 2276 debian@192.168.9.2
ssh -p 2276 debian@192.168.10.2
```

No se incluyen credenciales en este README. Use las credenciales administradas
del sistema de operacion.

Para editar una PocketBeagle con raiz normalmente de solo lectura:

```bash
sudo mount -o remount,rw /
# editar o copiar archivos
sudo mount -o remount,ro /
sync
```

La Raspberry Pi asigna interfaces e IPs segun los seriales USB en
`rpi/dist/scripts/config_ips_g84.sh`. Si se cambia una PocketBeagle, actualice
su serial en ese archivo.

## Espejo

El espejo tiene dos capas:

- `rpi/Espejo/g84_espejo.py`: control de hardware y servidor TCP `7777`.
- `rpi/Espejo/g84_espejo_mqtt.py`: puente MQTT.

El servidor acepta `ESTADO`, `METE`, `SACA`, `INIT` y `STOP`. La inicializacion
saca el espejo. El timeout de movimiento configurado es de `8 s`.

Consulta recomendada antes de mover:

```bash
source g84/fns_g84.sh
edoespejo
```

## Logger MQTT

El logger guarda `AR`, `DEC` y `FOCO` desde
`oan/control/84cm/guiador/motores/status` en SQLite.

```bash
cd g84/G84_Logger
./start.sh
./stop.sh
```

Ejecucion y utilidades manuales:

```bash
python3 mqtt_logger.py     # captura visible, duracion configurada de 12 h
python3 data2excel.py      # genera sensor_data.xlsx
python3 plot_data.py       # grafica datos
python3 clean_db.py        # elimina datos anteriores a la fecha configurada
```

Archivos generados:

- `mqtt_data.db`
- `mqtt_logger.pid`
- `nohup.out`
- `sensor_data.xlsx`

`clean_db.py` elimina registros permanentemente; haga respaldo antes de usarlo.

## Diagnostico y recuperacion

### Verificar conectividad

```bash
ping 192.168.0.239
ping 192.168.0.208
ping 192.168.8.2
ping 192.168.9.2
ping 192.168.10.2
```

### Verificar puertos

```bash
nc -vz 192.168.0.239 1883
nc -vz 192.168.0.208 9055
nc -vz 192.168.0.208 7777
nc -vz 192.168.9.2 9095
```

### Estado general

```bash
source g84/fns_g84.sh
edog84j
edoespejo
```

En la Raspberry Pi:

```bash
sudo supervisorctl status
bash rpi/estadorpi.sh
bash rpi/estadopockets.sh
```

### Recuperar comunicacion o reiniciar servicios

Desde la computadora de operacion:

```bash
./g84/recupera_comm.sh
./g84/soft_reset.sh
```

`recupera_comm.sh` reaplica la configuracion de interfaces y reinicia los
puentes MQTT. `soft_reset.sh` reaplica configuracion y recarga Supervisor.
Ambos usan `sshpass`; revise y proteja las credenciales embebidas antes de
publicar el repositorio.

### Logs

Los scripts EPL escriben principalmente en `/tmp`:

```text
/tmp/gscd.log
/tmp/consolad.consolad.log
/tmp/motorsguiad.log
/tmp/camgd.log
/tmp/http.server.log
```

Los servicios Supervisor actuales redirigen stdout/stderr a `/dev/null`. Para
diagnostico puede ser necesario cambiar temporalmente esta configuracion o
consultar el journal del sistema.

## Despliegue y configuracion

### Raspberry Pi

Directorio de trabajo documentado:

```text
/home/guiador/dist
```

Al arranque se ejecuta `rpi/dist/scripts/aplica.sh`, que llama
`aplica_dist.sh` y finalmente configura las interfaces PocketBeagle mediante
`config_ips_g84.sh`.

Crontab historico:

```cron
@reboot sh -c "cd /home/guiador/dist/scripts; bash aplica.sh > /dev/null"
```

La version actual usa Supervisor para mantener los servicios.

Archivos que normalmente deben revisarse al desplegar:

```text
rpi/dist/g84drvmqtt_edgar.py
rpi/dist/instruccionesguiador.py
rpi/dist/guiador84.cfg
rpi/dist/scripts/config_ips_g84.sh
rpi/Espejo/g84_espejo_mqtt.py
rpi/config/limites-motores-guiador-g84.json
rpi/config/offsets-cero-mecanicos-g84.json
```

### Configuracion EPL/UI

Revise:

```text
test_epl/epls/scripts/config_lugar.sh
test_epl/uiepls/scripts/config_lugar_ui.sh
```

Estos archivos contienen rutas absolutas y valores de host que pueden
sobrescribirse varias veces. En particular, `config_lugar_ui.sh` termina usando
`HOSTMQTT=localhost`; cambielo a `192.168.0.239` para operar contra el broker
del telescopio.

### Antes de publicar el repositorio

- Elimine o proteja contrasenas embebidas en scripts y documentos historicos.
- No publique bases SQLite, archivos Excel, logs, PID files ni entornos
  virtuales.
- Agregue un `.gitignore` para `venv3/`, `rpi/venv/`, `__pycache__/`,
  `*.pyc`, `*.db`, `*.xlsx`, `nohup.out`, `*.pid` y `.DS_Store`.
- Confirme que IPs, seriales USB, limites y centros correspondan a la
  instalacion activa.

## Archivos importantes

| Archivo | Funcion |
| --- | --- |
| `g84/fns_g84.sh` | Comandos de operacion Linux |
| `g84/fns_g84_mac.sh` | Comandos de operacion macOS |
| `g84/tuning pid.txt` | Notas y ejemplos de entonacion |
| `rpi/dist/g84drvmqtt_edgar.py` | Puente MQTT, limites y offsets |
| `rpi/dist/servg84_edgar_v2.py` | Servidor TCP principal |
| `rpi/dist/instruccionesguiador.py` | Interprete, conversiones y ejes |
| `rpi/dist/guiador84.cfg` | Entonacion persistente |
| `rpi/dist/ejeservo.py` | Comunicacion con servos |
| `rpi/dist/buscacentro.py` | Busqueda de centros |
| `rpi/Espejo/g84_espejo.py` | Servidor/control del espejo |
| `rpi/Espejo/g84_espejo_mqtt.py` | Puente MQTT del espejo |
| `test_epl/uiepls/motoresui/src/motgui-84.py` | UI principal de motores |
| `test_epl/uiepls/motoresui/src/ayuda-motores-guiador-84.txt` | Ayuda de la UI |
| `test_epl/uiepls/motoresui/src/centros-guiador-84` | Centros de instrumentos |
| `test_epl/tests/` | Pruebas unitarias |

---

Este README fue construido a partir del codigo y configuraciones versionadas.
Antes de una sesion de observacion, valide siempre la configuracion contra el
hardware instalado y el estado fisico real del guiador.
