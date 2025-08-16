#!/usr/bin/env python
import sys
import os
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"sys.path: {sys.path}")
try:
    import boto3
    print("boto3 imported successfully")
except ImportError as e:
    print(f"Failed to import boto3: {e}")

from botocore.config import Config
from dotenv import load_dotenv
import mimetypes

# Charger les variables d'environnement depuis .env
load_dotenv()

def upload_files_to_r2():
    """Uploade le contenu du répertoire staticfiles vers R2."""
    
    # Configuration de la session R2
    r2_config = Config(
        region_name='auto',
        s3={
            'addressing_style': 'virtual'
        }
    )
    
    # Création du client R2
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('R2_SECRET_ACCESS_KEY'),
        endpoint_url=os.environ.get('R2_ENDPOINT_URL'),
        config=r2_config
    )
    
    bucket_name = os.environ.get('R2_BUCKET_NAME')
    static_dir = 'pornflixe/staticfiles'  # Le répertoire où collectstatic a placé les fichiers

    if not bucket_name:
        print("❌ Erreur: La variable d'environnement R2_BUCKET_NAME n'est pas définie.")
        return

    if not os.path.isdir(static_dir):
        print(f"❌ Erreur: Le répertoire '{static_dir}' n'existe pas. Exécutez 'collectstatic' d'abord.")
        return

    print(f"🚀 Début de l'upload du répertoire '{static_dir}' vers le bucket '{bucket_name}'...")

    try:
        uploaded_count = 0
        for root, dirs, files in os.walk(static_dir):
            for filename in files:
                local_path = os.path.join(root, filename)
                
                # Détermine la clé S3 (chemin dans le bucket)
                relative_path = os.path.relpath(local_path, static_dir)
                s3_key = f"static/{relative_path}"

                # Détermine le ContentType
                content_type, _ = mimetypes.guess_type(local_path)
                if content_type is None:
                    content_type = 'application/octet-stream'

                print(f"  Uploading {local_path} to {s3_key}...")

                s3_client.upload_file(
                    local_path,
                    bucket_name,
                    s3_key,
                    ExtraArgs={
                        'ACL': 'public-read',
                        'ContentType': content_type
                    }
                )
                uploaded_count += 1
        
        print(f"\n🎉 {uploaded_count} fichiers uploadés avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'upload: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    upload_files_to_r2()
