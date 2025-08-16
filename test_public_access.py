#!/usr/bin/env python
import requests
import os
import django
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myauth.settings')
django.setup()

def test_public_access():
    """Teste l'accès public aux fichiers R2"""
    print("=== Test d'accès public aux fichiers R2 ===")
    
    try:
        # Créer un fichier de test
        test_content = ContentFile("Test d'accès public R2")
        test_filename = "public_test.txt"
        path = default_storage.save(test_filename, test_content)
        print(f"✅ Fichier de test créé: {path}")
        
        # Générer l'URL publique
        url = default_storage.url(path)
        print(f"🔗 URL publique: {url}")
        
        # Tester l'accès via HTTP
        print("\n🔎 Test d'accès HTTP...")
        response = requests.get(url)
        
        if response.status_code == 200:
            print("✅ Accès public réussi!")
            print(f"📄 Contenu: {response.text}")
        else:
            print(f"❌ Échec de l'accès public (Code: {response.status_code})")
            print(f"📝 Réponse: {response.text}")
            
        # Nettoyage
        default_storage.delete(path)
        print("\n🧹 Fichier de test supprimé")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_public_access()
