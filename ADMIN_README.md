# Administration de Pornflixe

## Interface d'administration moderne

Cette mise à jour apporte une interface d'administration complète et moderne avec les fonctionnalités suivantes :

### 1. Interface utilisateur améliorée
- Design moderne avec Tailwind CSS
- Barre de navigation latérale rétractable
- Tableau de bord avec statistiques et graphiques
- Formulaire épuré avec barre de progression pour les uploads
- Messages de feedback utilisateur

### 2. Gestion du contenu
- **Vidéos** : Ajout, modification, suppression, synchronisation avec Cloudflare R2
- **Photos** : Ajout, modification, suppression, synchronisation avec Cloudflare R2
- Publication programmée (date de publication)
- Mise en avant du contenu
- Barre de progression lors de l'upload

### 3. Gestion des utilisateurs
- Liste complète des utilisateurs avec recherche
- Détails utilisateur : informations, historique d'abonnement, contenu favori
- Activation/désactivation d'abonnement
- Statut utilisateur (actif/inactif)

### 4. Gestion des abonnements
- Création et gestion des plans d'abonnement
- Historique des abonnements utilisateurs
- Visualisation des abonnements expirant bientôt

### 5. Intégration Cloudflare R2
- Synchronisation individuelle de contenu
- Synchronisation en masse
- Statut de connexion et utilisation du stockage
- Boutons de synchronisation dans chaque formulaire

## Utilisation

### Accès à l'administration
1. Connectez-vous avec un compte administrateur
2. Accédez à `/config/admin-dashboard/` pour le tableau de bord

### Gestion du contenu
- **Vidéos** : `/config/admin/videos/`
- **Photos** : `/config/admin/photos/`

### Gestion des utilisateurs
- **Liste** : `/config/admin/users/`
- **Détails** : `/config/admin/users/<user_id>/`

### Gestion des abonnements
- **Liste** : `/config/admin/subscriptions/`
- **Ajout de plan** : `/config/admin/plans/add/`

## Fonctionnalités techniques

### Synchronisation R2
- Les fichiers sont automatiquement uploadés vers Cloudflare R2
- Vérification de l'existence des fichiers avant upload
- Gestion des erreurs de connexion

### Sécurité
- Accès restreint aux administrateurs uniquement
- Validation des formulaires
- Protection CSRF

### Performance
- Pagination des listes
- Recherche dans les listes
- Cache des requêtes fréquentes

## Personnalisation

### Modification de l'interface
- Templates dans `core/templates/administa/`
- Styles CSS personnalisés dans `base_admin.html`
- Scripts JavaScript dans les blocs `extra_js`

### Ajout de fonctionnalités
- Vues dans `core/views.py`
- URLs dans `core/urls.py`
- Modèles dans `core/models.py`

## Dépannage

### Problèmes de connexion R2
1. Vérifiez les variables d'environnement dans `.env`
2. Testez la connexion avec `python test_r2_connection.py`
3. Vérifiez les permissions de la clé API Cloudflare

### Problèmes d'upload
1. Vérifiez les permissions des dossiers de stockage
2. Vérifiez l'espace disponible
3. Consultez les logs d'erreur

## Maintenance

### Mise à jour des dépendances
```bash
pip install -r requirements.txt
```

### Collecte des fichiers statiques
```bash
python manage.py collectstatic
```

### Migration de la base de données
```bash
python manage.py makemigrations
python manage.py migrate
```