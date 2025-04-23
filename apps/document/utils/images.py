from PIL import Image, ExifTags
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

def rotate_image_if_needed(image_file):
    try:
        image = Image.open(image_file)
        original_format = image.format

        exif = image._getexif()
        orientation = None

        if exif:
            for tag, value in exif.items():
                if ExifTags.TAGS.get(tag) == "Orientation":
                    orientation = value
                    break

        rotate_values = {
            3: 180,
            6: 270,
            8: 90,
        }

        if orientation in rotate_values:
            image = image.rotate(rotate_values[orientation], expand=True)

            output = BytesIO()
            format_to_save = original_format if original_format in ['JPEG', 'PNG'] else 'JPEG'
            mime_type = f"image/{format_to_save.lower()}"

            image.save(output, format=format_to_save)
            output.seek(0)

            return InMemoryUploadedFile(
                output, 'ImageField', image_file.name, mime_type,
                output.getbuffer().nbytes, None
            )
    except Exception as e:
        print(f"[ROTATE] Error: {e}")

    return image_file
