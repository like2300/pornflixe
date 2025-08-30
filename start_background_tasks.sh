#!/bin/bash
# Script pour démarrer le processeur de tâches en arrière-plan

# Vérifier si le script est exécuté depuis le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "Erreur : Ce script doit être exécuté depuis le répertoire racine du projet Django."
    echo "Répertoire actuel : $(pwd)"
    exit 1
fi

echo "Démarrage du processeur de tâches en arrière-plan..."
echo "Ce processus doit être maintenu en exécution pour que les tâches asynchrones fonctionnent."
echo "Assurez-vous que vos identifiants R2 sont configurés dans les variables d'environnement."

# Démarrer le processeur de tâches
python manage.py process_tasks