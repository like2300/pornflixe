#!/usr/bin/env python
"""
Script de test pour vérifier la connexion à Cloudflare R2
"""

import os
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand

def test_r2_connection():
    """Teste la connexion à Cloudflare R2"""
    print("=== Test de connexion à Cloudflare R2 ===")
    
    # Vérifier les variables d'environnement
    required_vars = [
        'R2_ACCESS_KEY_ID',
        'R2_SECRET_ACCESS_KEY', 
        'R2_BUCKET_NAME',
        'R2_ENDPOINT_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables d'environnement manquantes: {', '.join(missing_vars)}")
        return False
    
    print("✅ Variables d'environnement trouvées")
    
    try:
        # Créer le client R2
        r2_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
            endpoint_url=os.getenv('R2_ENDPOINT_URL'),
            region_name='auto'
        )
        
        # Tester la liste des buckets
        response = r2_client.list_buckets()
        print("✅ Connexion réussie à R2")
        print(f"📊 Buckets disponibles: {[bucket['Name'] for bucket in response['Buckets']]}")
        
        # Tester l'accès au bucket spécifique
        bucket_name = os.getenv('R2_BUCKET_NAME')
        try:
            r2_client.head_bucket(Bucket=bucket_name)
            print(f"✅ Accès confirmé au bucket '{bucket_name}'")
        except ClientError as e:
            print(f"❌ Impossible d'accéder au bucket '{bucket_name}': {e}")
            return False
            
        # Tester l'upload d'un fichier de test
        test_content = b"Test de connexion R2 - Pornflixe"
        test_key = "test-connection.txt"
        
        r2_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content
        )
        print(f"✅ Fichier de test '{test_key}' uploadé avec succès")
        
        # Tester la récupération du fichier
        response = r2_client.get_object(
            Bucket=bucket_name,
            Key=test_key
        )
        content = response['Body'].read()
        if content == test_content:
            print("✅ Fichier de test récupéré avec succès")
        else:
            print("❌ Le contenu du fichier de test ne correspond pas")
            return False
            
        # Nettoyer le fichier de test
        r2_client.delete_object(
            Bucket=bucket_name,
            Key=test_key
        )
        print(f"✅ Fichier de test '{test_key}' supprimé")
        
        print("\n🎉 Tous les tests R2 ont réussi!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test R2: {e}")
        return False

if __name__ == "__main__":
    test_r2_connection()