# Upload de Vidéos vers Cloudflare R2

Cette fonctionnalité permet d'uploader des vidéos lourdes vers Cloudflare R2 avec suivi de la progression en temps réel.

## Configuration requise

1. Compte Cloudflare R2 avec un bucket configuré
2. Clés d'accès R2 configurées dans les variables d'environnement :
   - `R2_ACCESS_KEY_ID`
   - `R2_SECRET_ACCESS_KEY`
   - `R2_BUCKET_NAME`
   - `R2_ENDPOINT_URL`
   - `R2_CDN_DOMAIN` (optionnel)

## Démarrage

1. **Démarrer le processeur de tâches en arrière-plan :**
   ```bash
   ./start_background_tasks.sh
   ```

2. **Accéder à l'interface d'upload :**
   - Connectez-vous en tant qu'administrateur
   - Allez dans "Configuration" > "Vidéos" > "Upload avec progression"

## Fonctionnalités

- Upload asynchrone de vidéos lourdes
- Suivi de la progression en temps réel avec :
  - Pourcentage de transfert
  - Vitesse moyenne de transfert
  - Temps restant estimé
  - Temps total écoulé
- Interface utilisateur intuitive
- Gestion des erreurs

## Dépannage

### Problèmes courants

1. **Les tâches ne s'exécutent pas :**
   - Vérifiez que le processeur de tâches est en cours d'exécution
   - Vérifiez les logs pour les erreurs

2. **Erreurs d'authentification R2 :**
   - Vérifiez que vos identifiants R2 sont corrects
   - Vérifiez que le bucket existe et est accessible

3. **Erreurs de fichier :**
   - Vérifiez que le fichier vidéo est valide
   - Vérifiez les permissions d'écriture

### Vérification des logs

```bash
# Vérifier les logs de l'application
tail -f debug.log

# Vérifier les tâches en attente
python manage.py shell -c "from background_task.models import Task; print(Task.objects.all())"
```