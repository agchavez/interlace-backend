from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    generate_blob_sas
)
from datetime import datetime, timedelta
from django.conf import settings

def get_sas_url(blob_name: str):
    # blob_name = "path/en/el/container/archivo.jpg"
    container_name = settings.AZURE_CONTAINER
    account_name = settings.AZURE_ACCOUNT_NAME
    account_key = settings.AZURE_ACCOUNT_KEY

    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),  # Solo lectura
        expiry=datetime.utcnow() + timedelta(hours=1)  # Expira en 1 hora
    )

    # Arma la URL final
    return f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
