import boto3
import os
import time
from django.conf import settings
from django.core.files.storage import default_storage
from background_task import background
from .models import Video, VideoUpload
from botocore.exceptions import ClientError

# Initialisation du client R2
r2_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    region_name=settings.AWS_S3_REGION_NAME
)

CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks for multipart upload

@background(schedule=1)
def upload_video_to_r2(video_id):
    """
    Tâche asynchrone pour uploader une vidéo vers Cloudflare R2
    """
    try:
        # Récupération de la vidéo
        video = Video.objects.get(id=video_id)
        video_upload, created = VideoUpload.objects.get_or_create(video=video)
        
        # Mise à jour du statut
        video_upload.status = 'uploading'
        video_upload.save()
        
        # Chemin du fichier
        file_path = video.video.name
        file_key = f"videos/{video.id}/{os.path.basename(file_path)}"
        
        # Informations sur le fichier
        file_size = video.video.size
        start_time = time.time()
        
        # Initialisation de l'upload multipart
        try:
            multipart_upload = r2_client.create_multipart_upload(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=file_key
            )
            upload_id = multipart_upload['UploadId']
        except ClientError as e:
            video_upload.status = 'failed'
            video_upload.save()
            raise e
        
        # Liste des parts uploadées
        parts = []
        part_number = 1
        uploaded_bytes = 0
        
        # Ouverture du fichier
        # On vérifie d'abord si le fichier existe dans le stockage par défaut
        if default_storage.exists(file_path):
            with default_storage.open(file_path, 'rb') as f:
                while True:
                    # Lecture d'un chunk
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    # Upload de la part
                    try:
                        part = r2_client.upload_part(
                            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                            Key=file_key,
                            PartNumber=part_number,
                            UploadId=upload_id,
                            Body=chunk
                        )
                        
                        # Enregistrement de la part
                        parts.append({
                            'ETag': part['ETag'],
                            'PartNumber': part_number
                        })
                        
                        # Mise à jour de la progression
                        uploaded_bytes += len(chunk)
                        elapsed_time = int(time.time() - start_time)
                        video_upload.update_progress(uploaded_bytes, file_size, elapsed_time)
                        
                        part_number += 1
                        
                    except ClientError as e:
                        # Annulation de l'upload
                        r2_client.abort_multipart_upload(
                            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                            Key=file_key,
                            UploadId=upload_id
                        )
                        video_upload.status = 'failed'
                        video_upload.save()
                        raise e
        else:
            # Si le fichier n'existe pas, on marque l'upload comme échoué
            video_upload.status = 'failed'
            video_upload.save()
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas dans le stockage.")
        
        # Finalisation de l'upload
        try:
            r2_client.complete_multipart_upload(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=file_key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            
            # Mise à jour du statut
            video_upload.status = 'completed'
            video_upload.save()
            
        except ClientError as e:
            # Annulation de l'upload
            r2_client.abort_multipart_upload(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=file_key,
                UploadId=upload_id
            )
            video_upload.status = 'failed'
            video_upload.save()
            raise e
            
    except Video.DoesNotExist:
        # Gestion de l'erreur si la vidéo n'existe pas
        pass
    except Exception as e:
        # Gestion des autres erreurs
        if 'video_upload' in locals():
            video_upload.status = 'failed'
            video_upload.save()
        raise e