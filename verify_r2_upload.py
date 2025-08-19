import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from decouple import config
import uuid

def test_r2_upload():
    """
    Tests the connection and upload to a Cloudflare R2 bucket.
    """
    print("--- Lancement du test de connexion à Cloudflare R2 ---")

    try:
        # Load credentials from .env file
        access_key_id = config('R2_ACCESS_KEY_ID')
        secret_access_key = config('R2_SECRET_ACCESS_KEY')
        bucket_name = config('R2_BUCKET_NAME')
        endpoint_url = config('R2_ENDPOINT_URL')

        if not all([access_key_id, secret_access_key, bucket_name, endpoint_url]):
            print("❌ ERREUR: Une ou plusieurs variables d'environnement R2 sont manquantes dans le fichier .env.")
            print("Veuillez vérifier R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, R2_ENDPOINT_URL.")
            return

        print(f"🔧 Configuration chargée:")
        print(f"   - Bucket: {bucket_name}")
        print(f"   - Endpoint URL: {endpoint_url}")
        print(f"   - Access Key ID: {'*' * (len(access_key_id) - 4) + access_key_id[-4:]}")

        # Create a boto3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            endpoint_url=endpoint_url,
            region_name='auto'  # R2 specific
        )
        print("✅ Client Boto3 créé avec succès.")

        # Create a test file in memory
        test_content = "Ceci est un fichier de test pour vérifier la connexion à R2."
        test_file_name = f"test-upload-{uuid.uuid4()}.txt"
        
        print(f"\n📤 Tentative d'upload du fichier '{test_file_name}'...")

        # Upload the file
        s3_client.put_object(
            Bucket=bucket_name,
            Key=f"media/test_uploads/{test_file_name}",
            Body=test_content.encode('utf-8'),
            ContentType='text/plain',
            ACL='public-read'
        )
        
        print(f"✅ Fichier uploadé avec succès !")
        
        # Construct the public URL
        cdn_domain = config('R2_CDN_DOMAIN', default='').replace('https://', '').replace('http://', '')
        if cdn_domain:
            public_url = f"https://{cdn_domain}/media/test_uploads/{test_file_name}"
            print(f"\n🔗 URL publique pour vérification : {public_url}")
        else:
            print("\n⚠️ La variable R2_CDN_DOMAIN n'est pas définie. Impossible de construire l'URL publique.")

        print("\n--- Test terminé avec succès ---")

    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"❌ ERREUR DE CREDENTIALS: {e}")
        print("   Vérifiez que les clés d'accès sont correctes et bien chargées.")
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        error_message = e.response.get("Error", {}).get("Message")
        print(f"❌ ERREUR CLIENT BOTO3 ({error_code}): {error_message}")
        if error_code == 'InvalidAccessKeyId':
            print("   -> La clé 'R2_ACCESS_KEY_ID' est incorrecte.")
        elif error_code == 'SignatureDoesNotMatch':
            print("   -> La clé 'R2_SECRET_ACCESS_KEY' est incorrecte.")
        elif error_code == 'NoSuchBucket':
            print(f"   -> Le bucket '{bucket_name}' n'existe pas ou n'est pas accessible avec ces clés.")
        elif error_code == 'AccessDenied':
             print("   -> Accès refusé. Vérifiez les permissions de la clé API sur Cloudflare.")
        else:
            print(f"   -> Une erreur inattendue est survenue: {e}")
    except Exception as e:
        print(f"❌ ERREUR INATTENDUE: {e}")

if __name__ == "__main__":
    # Change directory to the script's location to find the .env file
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    test_r2_upload()
