# apps/core/storage_backends.py

from storages.backends.azure_storage import AzureStorage

class AzureMediaStorage(AzureStorage):
    azure_container = "tracker"
    expiration_secs = None  # o un número si querés que los enlaces expiren
