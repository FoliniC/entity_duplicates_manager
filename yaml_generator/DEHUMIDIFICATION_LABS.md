# Dehumidification Optimization Labs 🧪

Questo documento descrive la metodologia e le prove sperimentali in corso per ottimizzare la capacità di deumidificazione del sistema fancoil/PDC.

## 1. Il Problema: Andamento Altalenante
Dalle analisi dei log (31 Maggio 2026), si è riscontrato che l'umidità nelle stanze (Cucina, Sala, Corridoio) tende a oscillare o a salire nonostante il raffrescamento attivo.
- **Causa ipotizzata:** Il "toggling" frequente degli switch della ventola (cambi di velocità ogni 2-5 minuti) impedisce alla batteria di rimanere stabilmente sotto il punto di rugiada.
- **Effetto:** Ogni volta che la ventola si ferma o cambia bruscamente, la condensa sulla batteria si interrompe o viene parzialmente rievaporata.

## 2. L'Ipotesi di Lavoro
Per massimizzare la rimozione di acqua dall'aria (carico latente), è preferibile un **flusso d'aria lento ma costante**:
1. **Batteria Fredda:** Acqua refrigerata (10-14°C) sempre in circolazione.
2. **Ventilazione Continua:** Ventola fissa a Velocità 1 (Low/Silent).
3. **Tempo di Contatto:** L'aria lenta rimane più tempo a contatto con le alette fredde, massimizzando la condensa.

## 3. Setup Laboratorio: "Camera"
La stanza **Camera** è stata isolata come ambiente di test controllato per 24 ore.

### Configurazioni Applicate:
- **Forzatura Hardware (Fase 1 - 1 Giugno):** L'automazione `camera_automation.yaml` è stata impostata su `low` (Velocità 1). Risultato: Vantaggi minimi.
- **Forzatura Hardware (Fase 2 - 3 Giugno):** L'automazione `camera_automation.yaml` è stata modificata per mantenere il `fan_target` fisso su `medium` (Velocità 2).
- **Monitoraggio Differenziato:**
    - **Sensore A (Fancoil):** Lettura a 15-20 cm da terra (zona fredda/umida).
    - **Sensore B (TH3C):** Posizionato a 95 cm di altezza, lontano dal fancoil, per misurare il comfort reale nella "living zone".
    - **Sensore C (KNX):** Sensore a parete per riscontro temperatura ambiente.

### Logging Avanzato:
Il log `fancoil_events.log` è stato configurato per registrare ad ogni ciclo:
- Temperatura e Umidità TH3C.
- Temperatura e Umidità a bordo Fancoil.
- Stato della PDC e della Pompa di circolazione.

## 4. Obiettivi della Verifica (Domani Sera)
Valuteremo i grafici e i log cercando i seguenti indicatori di successo:
1. **Trend Discendente:** L'umidità a 95 cm (TH3C) deve mostrare una curva in calo costante, senza i "denti di sega" visti oggi.
2. **Delta Stratificazione:** Analisi della differenza tra l'umidità a terra e a 95 cm.
3. **Stabilità Termica:** Verificare che la velocità 2 costante sia sufficiente a mantenere il setpoint senza causare eccessivo freddo o ristagni di calore, e se la maggiore portata d'aria aiuti a superare i limiti visti con la velocità 1.

---
*Creato il: 31 Maggio 2026*
*Responsabile Test: Gemini CLI Laboratory*
