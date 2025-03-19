# documentos/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response

from apps.document.models.document import DocumentModel
from apps.document.serializers.document import DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = DocumentModel.objects.all()
    serializer_class = DocumentSerializer
