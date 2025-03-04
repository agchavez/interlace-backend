from rest_framework import serializers

from apps.document.models.document import DocumentModel


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentModel
        fields = [
            "id",
            "name",
            "file",  # generará la URL del archivo en Azure
            "extension",
            "type",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
