MN Laser Lab Manager - Browser Edition come servizio Windows
============================================================

Questa versione avvia il gestionale in background all'avvio di Windows, senza mostrare finestre CMD.

INSTALLAZIONE
-------------
1. Estrarre lo ZIP in una cartella stabile, ad esempio:
   C:\MN Laser Lab\

2. Fare tasto destro su:
   Installa_MN_Laser_Service.bat

3. Selezionare:
   Esegui come amministratore

4. Il servizio viene installato tramite Utilità di pianificazione di Windows:
   MN Laser Lab Manager Browser Service

5. Il browser NON viene aperto automaticamente all'avvio.
   Aprire manualmente:
   http://127.0.0.1:8000/

Da smartphone/tablet sulla stessa rete Wi-Fi:
   http://IP_DEL_PC:8000/

LOG
---
I log sono in:
%LOCALAPPDATA%\MN Laser Lab Manager\logs\browser_service.log

RIMOZIONE
---------
Eseguire come amministratore:
Rimuovi_MN_Laser_Service.bat
