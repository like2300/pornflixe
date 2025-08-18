#!/usr/bin/env python
import os
import boto3
from dotenv import load_dotenv
import sys

def get_s3_client():
    """Charge .env et retourne un client boto3 configuré."""
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(dotenv_path):
        print(f"❌ Erreur : Fichier .env non trouvé à : {dotenv_path}")
        return None
    load_dotenv(dotenv_path=dotenv_path)

    r2_access_key_id = os.getenv('R2_ACCESS_KEY_ID')
    r2_secret_access_key = os.getenv('R2_SECRET_ACCESS_KEY')
    r2_endpoint_url = os.getenv('R2_ENDPOINT_URL')
    
    if not all([r2_access_key_id, r2_secret_access_key, r2_endpoint_url]):
        print("❌ Erreur : Une ou plusieurs variables R2 sont manquantes dans votre .env.")
        return None

    return boto3.client(
        's3',
        aws_access_key_id=r2_access_key_id,
        aws_secret_access_key=r2_secret_access_key,
        endpoint_url=r2_endpoint_url,
        region_name='auto'
    )

def check_file_metadata(file_key):
    """Vérifie les métadonnées d'un fichier spécifique dans le bucket."""
    s3_client = get_s3_client()
    if not s3_client:
        return
        
    r2_bucket_name = os.getenv('R2_BUCKET_NAME')
    if not r2_bucket_name:
        print("❌ Erreur : R2_BUCKET_NAME n'est pas défini dans .env.")
        return

    print(f"▶️  Vérification des métadonnées pour le fichier : {file_key}")
    try:
        response = s3_client.head_object(Bucket=r2_bucket_name, Key=file_key)
        content_type = response.get('ContentType', 'Non défini')
        
        print("✅ Succès !")
        print(f"  - Content-Type : {content_type}")
        
        if content_type in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
            print("  - Verdict : Le Content-Type est correct pour une image.")
        else:
            print("  - ❗️ Verdict : Le Content-Type est INCORRECT. C'est la cause de votre problème.")

    except s3_client.exceptions.NoSuchKey:
        print(f"❌ Erreur : Le fichier '{file_key}' n'a pas été trouvé dans le bucket '{r2_bucket_name}'.")
    except Exception as e:
        print(f"❌ Une erreur est survenue : {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_to_check = sys.argv[1]
        check_file_metadata(file_to_check)
    else:
        print("ℹ️  Usage : python3 pornflixe/verify_r2_bucket.py <chemin/vers/le/fichier/dans/le/bucket.jpg>")
        print("Exemple : python3 pornflixe/verify_r2_bucket.py media/photos/gallery/image.jpg")