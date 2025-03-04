# documentos/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response

from apps.document.models.document import DocumentModel
from apps.document.serializers.document import DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = DocumentModel.objects.all()
    serializer_class = DocumentSerializer

    def create(self, request, *args, **kwargs):
        """
        Esperamos un multipart/form-data con 'archivo' y opcional 'nombre'
        Se subirá a Azure (gracias a django-storages).
        """
        file = request.FILES.get("file")
        name = request.data.get("name", "")
        if not file:
            return Response(
                {"detail": "Debe proveer un archivo en 'archivo'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        doc = DocumentModel(name=name if name else file.name)
        doc.file = file  # Se sube a Azure
        doc.save()
        serializer = self.get_serializer(doc)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
