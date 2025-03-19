from rest_framework import serializers
from apps.document.serializers.document import DocumentSerializer
from apps.imported.model.claim import ClaimModel


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

    claim_file = DocumentSerializer(read_only=True)
    credit_memo_file = DocumentSerializer(read_only=True)
    observations_file = DocumentSerializer(read_only=True)

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
            "created_at",
        ]
        read_only_fields = [
            "id", "status", "created_at", "assigned_to"
        ]