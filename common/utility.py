import os
from common.metaimage import MetaImage
import PIL
from shutil import copyfile
from io import BytesIO
from django.http import HttpResponse


def get_image_as_http_response(filename):
    _, extension = os.path.splitext(filename)
    if extension.lower() == '.mhd':
        reader = MetaImage(filename=filename)
        # Convert raw data to image, and then to a http response
        buffer = BytesIO()
        pil_image = reader.get_image()
        pil_image.save(buffer, "PNG")
    elif extension.lower() == '.png':
        buffer = BytesIO()
        pil_image = PIL.Image.open(filename)
        pil_image.save(buffer, "PNG")
    else:
        raise Exception('Uknown output image extension ' + extension)

    return HttpResponse(buffer.getvalue(), content_type="image/png")


def copy_image(filename, new_filename):
    _, original_extension = os.path.splitext(filename)
    _, new_extension = os.path.splitext(new_filename)

    # Read image
    if original_extension.lower() == '.mhd':
        metaimage = MetaImage(filename=filename)
        if new_extension.lower() == '.mhd':
            metaimage.write(new_filename)
        elif new_extension.lower() == '.png':
            pil_image = metaimage.get_image()
            pil_image.save(new_filename)
        else:
            raise Exception('Uknown output image extension ' + new_extension)
    elif original_extension.lower() == '.png':
        if new_extension.lower() == '.mhd':
            pil_image = PIL.Image.open(filename)
            metaimage = MetaImage(data=pil_image)
            metaimage.write(new_filename)
        elif new_extension.lower() == '.png':
            copyfile(filename, new_filename)
        else:
            raise Exception('Uknown output image extension ' + new_extension)
    else:
        raise Exception('Uknown input image extension ' + original_extension)


def create_folder(path):
    try:
        os.mkdir(path)  # Make dataset path if doesn't exist
    except:
        pass

    # Check that the path exists
    try:
        os.stat(path)
    except:
        return False, 'Failed to create directory at ' + path
