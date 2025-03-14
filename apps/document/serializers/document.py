import uuid
import os
from rest_framework import serializers
from apps.document.models.document import DocumentModel
from apps.document.utils.documents import get_sas_url

class DocumentSerializer(serializers.ModelSerializer):
    access_url = serializers.SerializerMethodField()

    class Meta:
        model = DocumentModel
        fields = [
            "id",
            "name",       # Aquí guardaremos el nombre original
            "file",       # Archivo en Azure
            "extension",
            "type",
            "created_at",
            "access_url", # URL (con SAS) para acceder al archivo
        ]
        read_only_fields = ["id", "created_at"]

    def get_access_url(self, obj):
        """
        Genera una URL con SAS (token de acceso temporal) si tu contenedor es privado.
        Así, el usuario podrá descargar con un enlace temporal.
        """
        if obj.file:
            return get_sas_url(obj.file.name)
        return None

    def create(self, validated_data):
        """
        - Conservamos 'name' con el nombre original.
        - Renombramos el 'file' para subirlo con UUID y evitar colisiones.
        """
        uploaded_file = validated_data.get("file", None)
        if uploaded_file:
            # Guardamos el nombre original en 'name' si no está en validated_data
            # (o si deseas forzarlo a ser el nombre del archivo).
            original_filename = uploaded_file.name
            if "name" not in validated_data or not validated_data["name"]:
                validated_data["name"] = original_filename

            # Extraer la extensión
            ext = ""
            if "." in original_filename:
                ext = original_filename.split(".")[-1]

            # Generar un nombre único
            new_filename = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())

            # Prefijar subcarpeta, por ejemplo "document/"
            new_path = os.path.join("document", new_filename)

            # Asignar el nombre único para el archivo
            uploaded_file.name = new_path

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Mismo proceso para cuando se actualiza el 'file'.
        """
        uploaded_file = validated_data.get("file", None)
        if uploaded_file:
            original_filename = uploaded_file.name
            if "name" not in validated_data or not validated_data["name"]:
                validated_data["name"] = original_filename

            ext = ""
            if "." in original_filename:
                ext = original_filename.split(".")[-1]

            new_filename = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())
            new_path = os.path.join("document", new_filename)
            uploaded_file.name = new_path

        return super().update(instance, validated_data)
