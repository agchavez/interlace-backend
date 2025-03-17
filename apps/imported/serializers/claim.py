from rest_framework import serializers
from apps.document.serializers.document import DocumentSerializer
from apps.imported.model.claim import ClaimModel

class ClaimSerializer(serializers.ModelSerializer):
    # Se muestran los documentos relacionados mediante el DocumentSerializer
    doc_trailer = DocumentSerializer(read_only=True)
    doc_descarga = DocumentSerializer(read_only=True)
    doc_contenido = DocumentSerializer(read_only=True)
    doc_producto = DocumentSerializer(read_only=True)

    class Meta:
        model = ClaimModel
        fields = [
            "id",
            "tracker",
            "assigned_to",
            "tipo",
            "descripcion",
            "status",
            "doc_trailer",
            "doc_descarga",
            "doc_contenido",
            "doc_producto",
            "created_at",
        ]
        read_only_fields = [
            "id", "status",
            "doc_trailer", "doc_descarga", "doc_contenido", "doc_producto",
            "created_at"
        ]
