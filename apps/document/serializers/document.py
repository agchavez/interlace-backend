import uuid
import re
from rest_framework import serializers
from apps.document.models.document import DocumentModel
from apps.document.utils.documents import get_sas_url


class DocumentSerializer(serializers.ModelSerializer):
    access_url = serializers.SerializerMethodField()

    class Meta:
        model = DocumentModel
        fields = [
            "id",
            "name",
            "file",
            "extension",
            "type",
            "created_at",
            "access_url",
            "folder",
            "subfolder"
        ]
        read_only_fields = ["id", "created_at", "access_url"]

    def get_access_url(self, obj):
        if obj.file:
            return get_sas_url(obj.file.name)
        return None

    def validate_folder(self, value):
        """
        Valida que el folder, si se proporciona, tenga entre 3 y 50 caracteres y
        contenga solo letras, números, guiones o guiones bajos.
        """
        if value:
            if not re.match(r'^[A-Za-z0-9_-]{3,50}$', value):
                raise serializers.ValidationError(
                    "El folder debe contener entre 3 y 50 caracteres y solo letras, números, guiones o guiones bajos."
                )
        return value

    def validate_subfolder(self, value):
        """
        Valida que la subcarpeta, si se proporciona, tenga entre 3 y 50 caracteres y
        contenga solo letras, números, guiones o guiones bajos.
        """
        if value:
            if not re.match(r'^[A-Za-z0-9_-]{3,50}$', value):
                raise serializers.ValidationError(
                    "La subcarpeta debe contener entre 3 y 50 caracteres y solo letras, números, guiones o guiones bajos."
                )
        return value

    def create(self, validated_data):
        uploaded_file = validated_data.get("file", None)

        if uploaded_file:
            original_filename = uploaded_file.name
            if not validated_data.get("name"):
                validated_data["name"] = original_filename

            ext = ""
            if "." in original_filename:
                ext = original_filename.split(".")[-1]

            folder = validated_data.get("folder", "general")
            subfolder = validated_data.get("subfolder", "")

            new_filename = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())

            if subfolder:
                new_path = f"document/{folder}/{subfolder}/{new_filename}"
            else:
                new_path = f"document/{folder}/{new_filename}"

            uploaded_file.name = new_path

        return super().create(validated_data)

    def update(self, instance, validated_data):
        uploaded_file = validated_data.get("file", None)

        if uploaded_file:
            original_filename = uploaded_file.name
            if not validated_data.get("name"):
                validated_data["name"] = original_filename

            ext = ""
            if "." in original_filename:
                ext = original_filename.split(".")[-1]

            folder = validated_data.get("folder", instance.folder)
            subfolder = validated_data.get("subfolder", instance.subfolder or "")

            new_filename = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())

            if subfolder:
                new_path = f"document/{folder}/{subfolder}/{new_filename}"
            else:
                new_path = f"document/{folder}/{new_filename}"

            uploaded_file.name = new_path

        return super().update(instance, validated_data)