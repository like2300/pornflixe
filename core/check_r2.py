# management/commands/check_r2.py
from django.core.management.base import BaseCommand
import boto3
from django.conf import settings

class Command(BaseCommand):
    help = 'Vérifie le contenu du bucket R2'

    def handle(self, *args, **options):
        s3 = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        try:
            response = s3.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            for obj in response.get('Contents', []):
                print(obj['Key'])
        except Exception as e:
            print(f'Erreur: {e}')