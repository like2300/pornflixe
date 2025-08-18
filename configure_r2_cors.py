#!/usr/bin/env python
import boto3
import os
from dotenv import load_dotenv

def configure_r2_cors():
    """
    Configure la politique CORS pour un bucket Cloudflare R2.
    Cette politique autorise les requêtes GET depuis n'importe quelle origine,
    ce qui est nécessaire pour que les navigateurs puissent afficher les images
    et autres médias stockés sur R2.
    """
    # Charger les variables d'environnement depuis le fichier .env
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(dotenv_path):
        print(f"❌ Erreur : Fichier .env non trouvé à l'emplacement : {dotenv_path}")
        print("Assurez-vous que le fichier .env est dans le même répertoire que ce script.")
        return
        
    load_dotenv(dotenv_path=dotenv_path)

    # Récupérer les informations d'identification R2 depuis les variables d'environnement
    r2_access_key_id = os.getenv('R2_ACCESS_KEY_ID')
    r2_secret_access_key = os.getenv('R2_SECRET_ACCESS_KEY')
    r2_endpoint_url = os.getenv('R2_ENDPOINT_URL')
    r2_bucket_name = os.getenv('R2_BUCKET_NAME')
    
    # Valider que toutes les variables nécessaires sont présentes
    required_vars = {
        'R2_ACCESS_KEY_ID': r2_access_key_id,
        'R2_SECRET_ACCESS_KEY': r2_secret_access_key,
        'R2_ENDPOINT_URL': r2_endpoint_url,
        'R2_BUCKET_NAME': r2_bucket_name
    }
    
    for var, value in required_vars.items():
        if not value:
            print(f"❌ Erreur : La variable d'environnement '{var}' n'est pas définie dans votre fichier .env.")
            return

    print(f"🔧 Configuration du CORS pour le bucket : {r2_bucket_name}")

    try:
        # Création du client S3 pour interagir avec R2
        s3_client = boto3.client(
            's3',
            aws_access_key_id=r2_access_key_id,
            aws_secret_access_key=r2_secret_access_key,
            endpoint_url=r2_endpoint_url,
            region_name='auto'  # R2 utilise 'auto'
        )

        # Définition de la politique CORS
        # 'AllowedOrigins': ['*'] est acceptable pour les contenus publics.
        # Pour plus de sécurité, vous pourriez le remplacer par l'URL de votre site,
        # par exemple : 'AllowedOrigins': ['https://votre-domaine.com']
        cors_configuration = {
            'CORSRules': [
                {
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'HEAD'],
                    'AllowedOrigins': ['*'],
                    'MaxAgeSeconds': 3600,
                }
            ]
        }

        # Application de la configuration CORS au bucket
        s3_client.put_bucket_cors(
            Bucket=r2_bucket_name,
            CORSConfiguration=cors_configuration
        )

        print("✅ La politique CORS a été appliquée avec succès !")
        print("Les images et les fichiers devraient maintenant se charger correctement dans le navigateur.")

    except Exception as e:
        print(f"❌ Une erreur est survenue lors de la configuration de CORS : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    configure_r2_cors()
