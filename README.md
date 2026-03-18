Markdown \# NuggetsManagement ♟️⛏️

\*\*NuggetsManagement\*\* è un software ad alte prestazioni per
l\'estrazione automatizzata, l\'analisi e la classificazione
(qualimetria) di \"pepite scacchistiche\" da enormi database di partite
in formato PGN.

Il progetto nasce a supporto di una ricerca accademica sulla computer
chess (premiata a livello internazionale) e ha lo scopo di fornire
dataset di posizioni critiche per l\'allenamento umano, il telegioco
(correspondence chess) e lo stress-test dei motori UCI basati su reti
neurali (NNUE).

\## 📖 Il Concetto di \"Pepita\" Una \*\*pepita\*\* è definita come una
posizione scacchistica caratterizzata da un elevato grado di tensione e
complessità dinamica. Invece di basarsi sulla tradizionale valutazione
in Centipawn (CP), il software filtra le posizioni utilizzando il
modello probabilistico \*\*Win/Draw/Loss (WDL)\*\*. Una posizione è
considerata una pepita se la probabilità di vittoria (WDL Expectation)
per una fazione si attesta su specifici target critici (es. 75% o 25%),
con un margine di tolleranza configurabile.

\## ✨ Caratteristiche Principali \* \*\*Elaborazione Asincrona:\*\*
Utilizza \`asyncio\` per lanciare istanze multiple del motore UCI in
parallelo, massimizzando l\'uso della CPU e abbattendo i tempi di I/O.
\* \*\*Filtro WDL Nativo:\*\* Interroga i motori moderni (come Stockfish
16+) sfruttando l\'opzione \`UCI_ShowWDL\`. \* \*\*Qualimetria
Avanzata:\*\* Calcola metriche complesse a costo computazionale \$O(1)\$
grazie all\'uso dei Bitboard: \* \*Fase della partita\* (Algoritmo di
Smirnov basato su materiale e semi-mosse). \* \*Tipo di Centro\*
(Aperto, Chiuso, Statico, Mobile, Dinamico con analisi di IQP e pedoni
sospesi). \* \*Tensione Tattica\* (conteggio catture legali istantanee).
\* \*Asimmetria di Materiale\*. \* \*\*Qualimetria Storica:\*\* Traccia
automaticamente la \*Frequenza\* (quante volte la pepita si presenta nel
database) e la \*Recenza\* (la data più recente in cui è stata giocata),
ignorando le analisi ridondanti grazie a una cache in RAM thread-safe.
\* \*\*Output Strutturato:\*\* Esporta i risultati in formati pronti per
l\'analisi dati (\`.jsonl\`, \`.csv\`).

\## 🛠️ Prerequisiti \* \*\*Motore UCI:\*\* Un eseguibile di Stockfish
(versione 16 o superiore) con supporto NNUE. \* Per lo sviluppo dal
codice sorgente: \*\*Python 3.9+\*\*.

\## 🚀 Installazione (Sviluppo) Se desideri eseguire il software dal
codice sorgente o modificarlo:

1\. Clona il repository: \`\`\`bash git clone
\[https://github.com/TUO-USERNAME/NuggetsManagement.git\](https://github.com/TUO-USERNAME/NuggetsManagement.git)
cd NuggetsManagement Crea e attiva un ambiente virtuale:

Bash python -m venv venv \# Su Windows: venv\\Scripts\\activate \# Su
Linux/macOS: source venv/bin/activate Installa le dipendenze:

Bash pip install -r requirements.txt 📦 Generazione dell\'Eseguibile
(Standalone) Puoi compilare NuggetsManagement in un unico file
eseguibile, in modo da poterlo distribuire a chi non ha Python
installato. Utilizziamo pyinstaller.

Assicurati di avere l\'ambiente virtuale attivo e installa PyInstaller:

Bash pip install pyinstaller Compila il progetto (il comando crea un
singolo file nascosto la finestra della console se non necessaria, ma in
questo caso ci serve per i log):

Su Windows:

Bash pyinstaller \--onefile \--name NuggetsManagement src/main.py Su
Linux:

Bash pyinstaller \--onefile \--name NuggetsManagement_linux src/main.py
Troverai il tuo eseguibile pronto all\'uso all\'interno della cartella
dist/. Potrai spostarlo ovunque sul tuo computer (ricordandoti di
fornirgli i file di configurazione o le cartelle necessarie).

📄 Licenza Questo progetto è distribuito sotto licenza MIT. Sentiti
libero di utilizzarlo, modificarlo e integrarlo nei tuoi progetti
(commerciali e non). Vedi il file LICENSE per i dettagli.

🎓 Riferimenti Accademici Il concetto teorico alla base dell\'estrazione
WDL e della qualimetria delle pepite ha vinto il primo premio alla
conferenza internazionale di Intelligenza Artificiale in Giappone. Link
al paper: Springer - 10.1007/978-3-032-02555-5_1

\-\--

Salva questo testo come \`README.md\` nella directory principale del tuo
progetto. Se vuoi, puoi subito fare un commit su GitHub per
cristallizzare il lavoro: \`\`\`bash git add README.md git commit -m
\"Aggiunto README.md con istruzioni di build\" git push origin main
