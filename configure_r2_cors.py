#!/usr/bin/env python
import boto3
from botocore.config import Config
import os
from django.conf import settings

def configure_r2_cors():
    """Configure les paramètres CORS pour le bucket R2"""
    
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
    
    # Configuration CORS
    cors_configuration = {
        'CORSRules': [
            {
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'HEAD'],
                'AllowedOrigins': ['*'],
                'MaxAgeSeconds': 3600
            }
        ]
    }
    
    try:
        # Application de la configuration CORS
        s3_client.put_bucket_cors(
            Bucket=os.environ.get('R2_BUCKET_NAME'),
            CORSConfiguration=cors_configuration
        )
        print("✅ Configuration CORS appliquée avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la configuration CORS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    configure_r2_cors()