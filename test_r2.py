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

def test_r2_connection():
    """Test la connexion à Cloudflare R2"""
    print("=== Test de connexion à Cloudflare R2 ===")
    
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
        # Test d'écriture d'un fichier
        print("\n📝 Test d'écriture d'un fichier...")
        content = ContentFile("Test de connexion à Cloudflare R2 - Test local")
        filename = "test_r2_local.txt"
        path = default_storage.save(filename, content)
        print(f"✅ Fichier enregistré: {path}")
        
        # Test de lecture du fichier
        print("\n📖 Test de lecture du fichier...")
        if default_storage.exists(path):
            file_content = default_storage.open(path).read()
            print(f"✅ Contenu lu: {file_content.decode('utf-8')}")
        else:
            print("❌ Fichier non trouvé")
            
        # Test d'URL
        print("\n🔗 Test de génération d'URL...")
        url = default_storage.url(path)
        print(f"✅ URL générée: {url}")
        
        # Vérification des paramètres de l'URL
        if 'pub-' in url and '.r2.dev' in url:
            print("✅ Format d'URL R2 correct")
        else:
            print("⚠️  Format d'URL R2 peut-être incorrect")
        
        # Nettoyage
        print("\n🧹 Nettoyage...")
        default_storage.delete(path)
        print("✅ Fichier supprimé")
        
        print("\n🎉 Tous les tests ont réussi!")
        print("\n🔧 Prochaines étapes:")
        print("1. Exécutez 'python manage.py collectstatic --noinput' pour uploader les fichiers statiques")
        print("2. Vérifiez dans l'interface R2 que les fichiers sont présents")
        print("3. Redémarrez votre serveur Django pour que les changements prennent effet")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_r2_connection()