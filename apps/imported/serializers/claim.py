from rest_framework import serializers
from apps.document.serializers.document import DocumentSerializer
from apps.imported.model.claim import ClaimModel, ClaimProductModel
from apps.maintenance.serializer.trailer import TrailerModelSerializer, TransporterModelSerializer
from apps.tracker.serializers import TrackerSerializer
from apps.document.models.document import DocumentModel


class ClaimProductSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_code = serializers.CharField(source="product.code", read_only=True)
    product_id = serializers.IntegerField(source="product.id", read_only=True)
    sap_code = serializers.CharField(source="product.sap_code", read_only=True)

    class Meta:
        model = ClaimProductModel
        fields = "__all__"
        read_only_fields = ["id", "product_id"]


class ClaimSerializer(serializers.ModelSerializer):
    # Serializamos las fotografías como listas de DocumentSerializer
    photos_container_closed = DocumentSerializer(many=True, read_only=True)
    photos_container_one_open = DocumentSerializer(many=True, read_only=True)
    photos_container_two_open = DocumentSerializer(many=True, read_only=True)
    photos_container_top = DocumentSerializer(many=True, read_only=True)
    photos_during_unload = DocumentSerializer(many=True, read_only=True)
    photos_pallet_damage = DocumentSerializer(many=True, read_only=True)
    photos_damaged_product_base = DocumentSerializer(many=True, read_only=True)
    photos_damaged_product_dents = DocumentSerializer(many=True, read_only=True)
    photos_damaged_boxes = DocumentSerializer(many=True, read_only=True)
    photos_grouped_bad_product = DocumentSerializer(many=True, read_only=True)
    photos_repalletized = DocumentSerializer(many=True, read_only=True)

    # Serializamos los documentos usando SerializerMethodField para manejar valores nulos
    claim_file = serializers.SerializerMethodField()
    credit_memo_file = serializers.SerializerMethodField()
    observations_file = serializers.SerializerMethodField()

    claim_products = ClaimProductSerializer(many=True, read_only=True)
    tracking = TrackerSerializer(read_only=True, many=False, source="tracker")
    trailer = TrailerModelSerializer(source='tracker.trailer', read_only=True)
    transporter = TransporterModelSerializer(source='tracker.transporter', read_only=True)

    class Meta:
        model = ClaimModel
        fields = [
            "id", "tracker", "assigned_to",
            "claim_type", "description", "status",
            "claim_number", "discard_doc", "observations",
            "claim_file", "credit_memo_file", "observations_file",
            "photos_container_closed", "photos_container_one_open",
            "photos_container_two_open", "photos_container_top",
            "photos_during_unload", "photos_pallet_damage",
            "photos_damaged_product_base", "photos_damaged_product_dents",
            "photos_damaged_boxes", "photos_grouped_bad_product",
            "photos_repalletized",
            "created_at","claim_products", "tracking", "trailer", "transporter"
        ]
        read_only_fields = [
            "id", "status", "created_at", "assigned_to", "trailer", "transporter"
        ]
    def get_claim_file(self, obj):
        if obj.claim_file and obj.claim_file.name:
            try:
                document = DocumentModel.objects.get(file=obj.claim_file.name)
                return DocumentSerializer(document).data
            except DocumentModel.DoesNotExist:
                return None
        return None

    def get_credit_memo_file(self, obj):
        if obj.credit_memo_file and obj.credit_memo_file.name:
            try:
                document = DocumentModel.objects.get(file=obj.credit_memo_file.name)
                return DocumentSerializer(document).data
            except DocumentModel.DoesNotExist:
                return None
        return None

    def get_observations_file(self, obj):
        if obj.observations_file and obj.observations_file.name:
            try:
                document = DocumentModel.objects.get(file=obj.observations_file.name)
                return DocumentSerializer(document).data
            except DocumentModel.DoesNotExist:
                return None
        return None
