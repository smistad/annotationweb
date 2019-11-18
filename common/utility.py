import os
from common.metaimage import MetaImage
import PIL
from shutil import copyfile
from io import BytesIO
from django.http import HttpResponse
import numpy as np
from annotationweb.post_processing import post_processing_register
import time

def get_image_as_http_response(filename, post_processing_method=''):
    _, extension = os.path.splitext(filename)
    buffer = BytesIO()
    start = time.time()
    if extension.lower() == '.mhd':
        reader = MetaImage(filename=filename)
        # Convert raw data to image, and then to a http response
        pil_image = reader.get_image()
        spacing = reader.get_spacing()
        if spacing[0] != spacing[1]:
            # Compensate for anistropic pixel spacing
            real_aspect = pil_image.width*spacing[0] / (pil_image.height*spacing[1])
            current_aspect = float(pil_image.width) / pil_image.height
            new_width = int(pil_image.width*(real_aspect / current_aspect))
            new_height = pil_image.height
            pil_image = pil_image.resize((new_width, new_height))
    elif extension.lower() == '.png':
        pil_image = PIL.Image.open(filename)
    else:
        raise Exception('Unknown output image extension ' + extension)

    if post_processing_method is not '':
        post_processing = post_processing_register.get(post_processing_method)
        new_image = post_processing.post_process(np.asarray(pil_image))
        if len(new_image.shape) > 2 and new_image.shape[2] == 3:
            pil_image = PIL.Image.fromarray(new_image, 'RGB')
        else:
            pil_image = PIL.Image.fromarray(new_image, 'L')

    print('Image loading time', time.time() - start, 'seconds')
    pil_image.save(buffer, "PNG", compress_level=1)  # TODO This function is very slow due to PNG compression
    print('Image loading time with save to buffer', time.time() - start, 'seconds')

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
            raise Exception('Unknown output image extension ' + new_extension)
    elif original_extension.lower() == '.png':
        if new_extension.lower() == '.mhd':
            pil_image = PIL.Image.open(filename)
            metaimage = MetaImage(data=np.asarray(pil_image))
            metaimage.write(new_filename)
        elif new_extension.lower() == '.png':
            copyfile(filename, new_filename)
        else:
            raise Exception('Unknown output image extension ' + new_extension)
    else:
        raise Exception('Unknown input image extension ' + original_extension)


def create_folder(path):
    os.makedirs(path, exist_ok=True)
