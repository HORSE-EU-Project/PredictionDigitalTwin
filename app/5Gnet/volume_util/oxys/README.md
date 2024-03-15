# 
# PROGETTO: E2E Fiber&5G
# PROTOTIPO 5G FWA Peripheral Test Unit (PTU) v1.0 (28 Settembre 2022)
#
# Software per misurazione banda e latenza su reti 4G/5G tramite container
# DISI - Universita' di Trento
#
# Author: Fabrizio Granelli (fabrizio.granelli@unitn.it)
#

Descrizione software:
=====================
Software per la misurazione tramite container delle prestazioni di una
rete 4G/5G a livello applicazione.
Il software rappresenta un prototipo da laboratorio, che verra' 
ulteriormente aggiornato e migliorato durante la fase finale del
progetto. Viene rilasciato per uso interno ad OXYS S.r.l.

Descrizione file di progetto:
=============================
Dockerfile
- contiene le istruzioni per la creazione del container di misurazione
  (sia client che server, il container e' unico)

build_image.sh
- script per facilitare la creazione del container docker in locale

running_twamp.sh
- esempio di deploy locale di client e server ed esecuzione delle misure
  (al termine i container restano attivi in background e si puo' 
  interagire con essi) 

stop_twamp.sh
- script per terminare tutti i container docker nel sistema
  (da eseguire dopo 'running_twamp.sh')

backup_dockerhub.sh, backup_azure.sh
- script per caricare il container di progetto su docker hub ed azure

azure-start.sh, azure-stop.sh, running_server_azure.sh
- work in progress preliminare per lo sviluppo di un testbed end-to-end
  su cloud (al momento solo sperimentale)

azure-doc/
- directory con documentazione per l'uso di MS Azure

iperf3/
- directory con i file sorgenti per l'uso di iperf per la misurazione 
  della banda disponibile

twamp/
- directory con i file sorgenti per l'implementazione di TWAMP

webserver/
- directory con i file sorgenti per l'implementazione dell'interfaccia
  HTTP
