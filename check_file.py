
import os
import boto3
from botocore.exceptions import ClientError
from decouple import config

def check_file_on_r2(file_name):
    """
    Checks if a specific file exists in the Cloudflare R2 bucket.
    """
    print("--- Lancement de la vérification sur Cloudflare R2 ---")
    try:
        access_key_id = config('R2_ACCESS_KEY_ID')
        secret_access_key = config('R2_SECRET_ACCESS_KEY')
        bucket_name = config('R2_BUCKET_NAME')
        endpoint_url = config('R2_ENDPOINT_URL')

        if not all([access_key_id, secret_access_key, bucket_name, endpoint_url]):
            print("❌ ERREUR: Variables d'environnement R2 manquantes.")
            return

        print(f"🔧 Connexion au bucket : {bucket_name}")

        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            endpoint_url=endpoint_url,
            region_name='auto'
        )

        print(f"🔍 Recherche du fichier '{file_name}'...")

        # On liste tous les objets (fichiers) dans le bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' in response:
            for obj in response['Contents']:
                # On vérifie si le nom du fichier est dans la clé (chemin complet) de l'objet
                if file_name in obj['Key']:
                    print(f"\n✅ TROUVÉ ! Le fichier a été trouvé sur R2 :")
                    print(f"   - Chemin complet : {obj['Key']}")
                    print(f"   - Date de modification : {obj['LastModified']}")
                    print(f"   - Taille : {obj['Size']} bytes")
                    print("\n--- Vérification terminée avec succès ---")
                    return

        print(f"\n❌ NON TROUVÉ. Le fichier '{file_name}' n'a pas été trouvé dans le bucket.")
        print("--- Vérification terminée ---")

    except ClientError as e:
        print(f"❌ ERREUR CLIENT BOTO3: {e.response['Error']['Message']}")
    except Exception as e:
        print(f"❌ ERREUR INATTENDUE: {e}")

if __name__ == "__main__":
    # Assurez-vous que le script trouve le .env dans le bon dossier
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Le nom du fichier à vérifier
    file_to_check = "device-mockup_6x_postspark_2025-08-18_00-05-33.png"
    check_file_on_r2(file_to_check)
