#!/usr/bin/env python
import os
import django
from django.conf import settings
from django.core.management import execute_from_command_line
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myauth.settings')
django.setup()

def check_r2_files():
    """Vérifie si les fichiers sont bien uploadés vers R2"""
    print("=== Vérification des fichiers dans Cloudflare R2 ===")
    
    # Vérifier la configuration
    print(f"DEBUG: {settings.DEBUG}")
    print(f"USE_R2_IN_DEBUG: {getattr(settings, 'USE_R2_IN_DEBUG', False)}")
    print(f"DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Non défini')}")
    print(f"AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Non défini')}")
    print(f"AWS_S3_ENDPOINT_URL: {getattr(settings, 'AWS_S3_ENDPOINT_URL', 'Non défini')}")
    print(f"AWS_S3_CUSTOM_DOMAIN: {getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', 'Non défini')}")
    
    # Vérifier si R2 est activé (en DEBUG ou en production)
    use_r2 = (not settings.DEBUG) or getattr(settings, 'USE_R2_IN_DEBUG', False)
    
    if not use_r2:
        print("\n⚠️  Attention: La configuration R2 n'est pas activée.")
        print("Pour tester R2 en local, définissez USE_R2_IN_DEBUG=True dans votre fichier .env")
        return
    
    try:
        # Lister les fichiers dans le bucket
        print("\n📂 Contenu du bucket R2:")
        # Créer un fichier de test temporaire
        test_content = ContentFile("Test de vérification R2")
        test_filename = "test_verification.txt"
        path = default_storage.save(test_filename, test_content)
        print(f"✅ Fichier de test créé: {path}")
        
        # Vérifier l'existence du fichier
        if default_storage.exists(path):
            print("✅ Le système de stockage R2 fonctionne correctement")
            
            # Générer l'URL
            url = default_storage.url(path)
            print(f"🔗 URL du fichier de test: {url}")
            
            # Nettoyage
            default_storage.delete(path)
            print("🧹 Fichier de test supprimé")
        else:
            print("❌ Le système de stockage R2 ne fonctionne pas correctement")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()

def list_static_files():
    """Liste les fichiers statiques dans le répertoire local"""
    print("\n=== Fichiers statiques locaux ===")
    static_root = settings.STATIC_ROOT
    if os.path.exists(static_root):
        print(f"📂 Répertoire staticfiles: {static_root}")
        # Compter les fichiers
        file_count = 0
        for root, dirs, files in os.walk(static_root):
            file_count += len(files)
        print(f"📄 Nombre de fichiers: {file_count}")
    else:
        print(f"❌ Répertoire staticfiles introuvable: {static_root}")

if __name__ == "__main__":
    check_r2_files()
    list_static_files()
