IFT3325 - Devoir 2
Automne 2025

Membres de l'équipe :
-Willis NOMENA ANDRE 20213162

Description :
Ce projet implémente un protocole de liaison de données fiable (Go-Back-N) sur un canal simulé non fiable.

Structure des fichiers :
- code/
  - canal.py      : Simulation du canal (erreurs, pertes, délais).
  - stuffing.py   : Fonctions de bit-stuffing et CRC.
  - protocole.py  : Implémentation de l'émetteur, du récepteur et des scénarios de test.
- message.txt     : Fichier source pour la transmission.
- rapport.md      : Rapport détaillé des choix de conception et des résultats.

Prérequis :
- Python 3.x

Instructions d'exécution :
1. Placez-vous dans le dossier `code/`.
2. Exécutez la commande : `python protocole.py`
3. Les résultats des 4 scénarios s'afficheront dans le terminal.
4. Le fichier reçu sera reconstitué dans `output.txt` (dans le dossier d'exécution).

Paramètres :
Les scénarios sont configurés dans le bloc `if __name__ == "__main__":` à la fin de `protocole.py`.
Vous pouvez modifier les probabilités d'erreur, de perte et les délais directement dans ces appels.
