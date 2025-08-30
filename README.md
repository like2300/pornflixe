# PornFlixe

## Fonctionnalité d'upload de vidéos avec progression en temps réel

Ce projet inclut une fonctionnalité avancée d'upload de vidéos vers Cloudflare R2 avec suivi de la progression en temps réel.

### Fonctionnalités

- Upload asynchrone de vidéos lourdes vers Cloudflare R2
- Barre de progression en temps réel avec :
  - Pourcentage de transfert
  - Vitesse moyenne de transfert
  - Temps restant estimé
  - Temps total écoulé
- Interface utilisateur intuitive avec mise à jour automatique via Ajax
- Gestion des erreurs et états de l'upload

### Technologies utilisées

- Django (Python 3.x)
- Cloudflare R2 (via `boto3`)
- Gestion asynchrone avec `django-background-tasks`
- JavaScript pour les mises à jour en temps réel

### Installation

1. Installer les dépendances :
   ```bash
   pip install django-background-tasks boto3
   ```

2. Ajouter `background_task` aux `INSTALLED_APPS` dans `settings.py`

3. Exécuter les migrations :
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

### Configuration de Cloudflare R2

Avant d'utiliser l'upload, configurez vos identifiants R2 dans les variables d'environnement :

```bash
export R2_ACCESS_KEY_ID="votre_access_key"
export R2_SECRET_ACCESS_KEY="votre_secret_key"
export R2_BUCKET_NAME="votre_bucket"
export R2_ENDPOINT_URL="https://votre_compte.r2.cloudflarestorage.com"
export R2_CDN_DOMAIN="votre_domaine_cdn"  # Optionnel
```

### Utilisation

1. Démarrer le processeur de tâches en arrière-plan :
   ```bash
   ./start_background_tasks.sh
   ```

2. Accéder à l'interface d'upload via l'administration :
   - Aller dans "Configuration" > "Vidéos"
   - Cliquer sur "Upload avec progression"

3. Suivre la progression en temps réel pendant l'upload

### Personnalisation

Les paramètres de l'upload peuvent être ajustés dans `core/tasks.py` :
- `CHUNK_SIZE` : Taille des morceaux pour l'upload multipart

### Documentation détaillée

Pour plus d'informations sur l'utilisation de l'upload, consultez [UPLOAD_README.md](UPLOAD_README.md)
