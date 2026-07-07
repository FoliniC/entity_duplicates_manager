#!/bin/bash
# Script per aggiornare Google Antigravity CLI (agy) su Debian 13

set -e

echo "=== Aggiornamento di Google Antigravity CLI ==="

# Verifica se curl è installato
if ! command -v curl &> /dev/null; then
    echo "Errore: curl non è installato. Installazione in corso (richiede privilegi di root)..."
    sudo apt-get update && sudo apt-get install -y curl
fi

# Prova prima ad utilizzare il comando integrato agy self-update o agy update
if command -v agy &> /dev/null; then
    echo "Rilevata installazione esistente di agy."
    echo "Tentativo di aggiornamento tramite comando integrato..."
    if agy update; then
        echo "Aggiornamento completato con successo tramite 'agy update'."
        agy --version
        exit 0
    else
        echo "Metodo 'agy update' non riuscito o non supportato. Eseguo il download dello script ufficiale..."
    fi
else
    echo "Nessuna installazione locale di agy rilevata. Installazione iniziale in corso..."
fi

# Aggiornamento/installazione tramite script ufficiale
echo "Download ed esecuzione dello script di installazione ufficiale..."
curl -fsSL https://antigravity.google/cli/install.sh | bash

echo "=== Verifica della nuova versione ==="
if command -v agy &> /dev/null; then
    echo "Antigravity CLI installato correttamente!"
    agy --version
else
    # Verifica nei percorsi comuni nel caso in cui non sia ancora nel PATH corrente
    if [ -f "$HOME/.local/bin/agy" ]; then
        echo "Trovato in $HOME/.local/bin/agy. Assicurati che sia nel tuo PATH."
        "$HOME/.local/bin/agy" --version
    elif [ -f "/usr/local/bin/agy" ]; then
        echo "Trovato in /usr/local/bin/agy."
        "/usr/local/bin/agy" --version
    else
        echo "Attenzione: l'eseguibile 'agy' non è stato trovato nel PATH corrente dopo l'installazione."
    fi
fi
