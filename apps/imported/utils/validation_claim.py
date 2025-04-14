# apps/imported/utils/validate_claim.py
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.imported.model.claim import ClaimModel, CLAIM_STATUS_CHOICES, ClaimTypeModel
from apps.imported.exceptions.claim import (
    ClaimTypeInvalid, ClaimDescriptionRequired, ClaimTrackerRequired,
    ClaimStatusInvalid, ClaimStatusTransitionInvalid, FileTooLarge,
    UnsupportedFileType, TooManyPhotos, PhotoRequiredForDamage, ClaimAlreadyExists
)
from apps.tracker.exceptions.tracker import UserWithoutDistributorCenter
from apps.tracker.models import TrackerModel

User = get_user_model()


def validate_create_claim(request, tracker_id=None, claim_id=None):
    """
    Validates data for creating or updating a claim

    Args:
        request: The HTTP request
        tracker_id: Optional tracker ID if creating a new claim
        claim_id: Optional claim ID if updating existing claim

    Returns:
        tuple: (user, tracker, claim) if validation passes

    Raises:
        Various exceptions for validation errors
    """
    user = request.user
    distributor_center = user.centro_distribucion
    data = request.data

    # Validate user has a distribution center
    if distributor_center is None:
        raise UserWithoutDistributorCenter()

    # Get tracker instance if tracker_id provided
    tracker = None
    if tracker_id:
        try:
            tracker = TrackerModel.objects.get(pk=tracker_id)
        except TrackerModel.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound(detail="Tracker no encontrado")

    if not claim_id and hasattr(tracker, 'claim') and tracker.claim is not None:
        raise ClaimAlreadyExists()
    # Get claim instance if claim_id provided
    claim = None
    if claim_id:
        try:
            claim = ClaimModel.objects.get(pk=claim_id)
            tracker = claim.tracker  # Get tracker from claim
        except ClaimModel.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound(detail="Reclamo no encontrado")

    # If both are missing, we can't proceed
    if not tracker and not claim:
        raise ClaimTrackerRequired()

    # Validate claim type if provided
    claim_type = data.get("claim_type") or data.get("tipo")
    try:
        print("claim_type", claim_type)
        claim_type = ClaimTypeModel.objects.filter(id=int(claim_type)).first()
        print("claim_type", claim_type)
    except ClaimTypeModel.DoesNotExist:
        raise ClaimTypeInvalid()

    # Validate document files (size and type)
    validate_document_files(request.FILES)

    # If claim type is DAÑOS_CALIDAD_TRANSPORTE, validate required photos
    # if claim_type == "DAÑOS_CALIDAD_TRANSPORTE":
    #     validate_damage_photos(request.FILES)

    # Return validated user, tracker and claim (if applicable)
    return (user, tracker, claim)


def validate_document_files(files):
    """
    Validates document files for size and type
    """
    # Validate document files
    doc_fields = ['claim_file', 'credit_memo_file', 'observations_file']

    for field in doc_fields:
        if field in files:
            file_obj = files[field]
            # Check file size (5MB limit for documents)
            if file_obj.size > 15 * 1024 * 1024:
                raise FileTooLarge()

            # Check file type for documents
            file_name = file_obj.name.lower()
            file_extension = file_name.split('.')[-1] if '.' in file_name else ''

            if file_extension not in ['pdf', 'xlsx', 'xls']:
                raise UnsupportedFileType()

    # Validate photo files
    photo_categories = [
        "photos_container_closed", "photos_container_one_open",
        "photos_container_two_open", "photos_container_top",
        "photos_during_unload", "photos_pallet_damage",
        "photos_damaged_product_base", "photos_damaged_product_dents",
        "photos_damaged_boxes", "photos_grouped_bad_product",
        "photos_repalletized", "photos_production_batch"
    ]

    for category in photo_categories:
        if category in files:
            photo_files = files.getlist(category)

            # Check number of photos (max 3 per category)
            if len(photo_files) > 3:
                raise TooManyPhotos()

            for photo in photo_files:
                # Check file size (2MB limit for photos)
                if photo.size > 10 * 1024 * 1024:
                    raise FileTooLarge()

                # Check file type for photos
                file_name = photo.name.lower()
                file_extension = file_name.split('.')[-1] if '.' in file_name else ''

                if file_extension not in ['jpg', 'jpeg', 'png', 'gif']:
                    raise UnsupportedFileType()


def validate_damage_photos(files):
    """
    Validates that required photos are present for damage claims
    """
    # For DAÑOS_CALIDAD_TRANSPORTE, at least one photo in each damage category is required
    damage_categories = [
        "photos_damaged_product_base",
        "photos_damaged_product_dents",
        "photos_damaged_boxes",
        "photos_grouped_bad_product",
        "photos_repalletized"
    ]

    for category in damage_categories:
        if category not in files or len(files.getlist(category)) == 0:
            raise PhotoRequiredForDamage()


def validate_update_claim_status(claim_id, new_status, user=None):
    """
    Validates that a claim status change is valid

    Args:
        claim_id: ID of the claim to update
        new_status: The new status value
        user: Optional user making the change

    Returns:
        ClaimModel: The claim instance if validation passes

    Raises:
        Various exceptions for validation errors
    """
    try:
        claim = ClaimModel.objects.get(pk=claim_id)
    except ClaimModel.DoesNotExist:
        from rest_framework.exceptions import NotFound
        raise NotFound(detail="Reclamo no encontrado")

    # Validate the status is valid
    valid_statuses = [choice[0] for choice in CLAIM_STATUS_CHOICES]
    if new_status not in valid_statuses:
        raise ClaimStatusInvalid()

    # Define valid transitions (from -> to)
    valid_transitions = {
        "PENDIENTE": ["EN_REVISION", "RECHAZADO", "APROBADO"],
        "EN_REVISION": ["PENDIENTE", "RECHAZADO", "APROBADO"],
        "RECHAZADO": ["PENDIENTE", "EN_REVISION"],
        "APROBADO": ["PENDIENTE", "EN_REVISION"]
    }

    # Check if the transition is valid
    if new_status != claim.status and new_status not in valid_transitions.get(claim.status, []):
        raise ClaimStatusTransitionInvalid()

    # If user is provided, check if they have permission to change status
    if user and not user.has_perm('imported.change_claimmodel'):
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("No tienes permiso para cambiar el estado de este reclamo")

    return claim