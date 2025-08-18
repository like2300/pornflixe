#!/usr/bin/env python
import os
import boto3
from dotenv import load_dotenv

def list_all_bucket_files():
    """Se connecte au bucket R2 et liste TOUS les objets."""
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(dotenv_path):
        print(f"❌ Erreur : Fichier .env non trouvé à : {dotenv_path}")
        return
    load_dotenv(dotenv_path=dotenv_path)

    r2_bucket_name = os.getenv('R2_BUCKET_NAME')
    print(f"▶️  Tentative de lister tous les fichiers du bucket '{r2_bucket_name}'...")

    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
            endpoint_url=os.getenv('R2_ENDPOINT_URL'),
            region_name='auto'
        )

        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=r2_bucket_name)

        found_files = False
        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    found_files = True
                    print(f"  - {obj['Key']}")
            else:
                break # No more contents

        if not found_files:
            print("ℹ️  Le bucket est vide.")
        else:
            print("✅ Liste terminée.")

    except Exception as e:
        print(f"❌ Une erreur est survenue : {e}")

if __name__ == "__main__":
    list_all_bucket_files()
