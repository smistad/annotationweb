import zlib
import numpy as np
import PIL
import os


class MetaImageReader:
    def __init__(self, filename):
        if not os.path.isfile(filename):
            raise Exception('File ' + filename + ' does not exist')

        self.attributes = {}
        self.base_path = os.path.dirname(filename) + '/'
        # Parse file
        with open(filename, 'r') as f:
            for line in f:
                parts = line.split('=')
                if len(parts) != 2:
                    raise Exception('Unable to parse metaimage file')
                self.attributes[parts[0].strip()] = parts[1].strip()

    def get_size(self):
        dims = self.attributes['DimSize'].split(' ')
        return (int(dims[0]), int(dims[1]))

    def get_raw_filename(self):
        return self.base_path + self.attributes['ElementDataFile']

    def get_pixel_data(self):
        if self.attributes['CompressedData'] == 'True':
            # Read compressed raw file (.zraw)
            with open(self.get_raw_filename(), 'rb') as raw_file:
                raw_data_compressed = raw_file.read()
                raw_data_uncompressed = zlib.decompress(raw_data_compressed)
                return np.fromstring(raw_data_uncompressed, dtype=np.uint8)
        else:
            # Read uncompressed raw file (.raw)
            return np.fromfile(self.get_raw_filename(), dtype=np.uint8)

    def get_image(self):
        pil_image = PIL.Image.new('L', self.get_size(), color='white')
        pil_image.putdata(self.get_pixel_data())

        return pil_image


def tuple_to_string(tuple):
    string = ''
    for i in range(len(tuple)):
        string += str(tuple[i]) + ' '
    return string[:len(string)-1]


class MetaImageWriter:
    def __init__(self, filename, data):
        self.attributes = {}
        self.base_path = os.path.dirname(filename) + '/'
        self.filename = os.path.basename(filename)
        self.ndims = len(data.shape)
        self.dim_size = data.shape
        self.data = data

    def set_attribute(self, key, value):
        self.attributes[key] = value

    def set_spacing(self, spacing):
        if len(spacing) != 2 or len(spacing) != 3:
            raise ValueError('Spacing must have 2 or 3 components')
        self.attributes['ElementSpacing'] = spacing

    def get_metaimage_type(self):
        np_type = self.data.dtype
        if np_type == np.float32:
            return 'MET_FLOAT'
        elif np_type == np.uint8:
            return 'MET_UCHAR'
        elif np_type == np.int8:
            return 'MET_CHAR'
        elif np_type == np.uint16:
            return 'MET_USHORT'
        elif np_type == np.int16:
            return 'MET_SHORT'
        elif np_type == np.uint32:
            return 'MET_UINT'
        elif np_type == np.int32:
            return 'MET_INT'
        else:
            raise ValueError('Unknown numpy type')

    def write(self):
        raw_filename = self.filename[:self.filename.rfind('.')] + '.raw'
        # Write meta image file
        with open(self.base_path + self.filename, 'w') as f:
            f.write('NDims = ' + str(self.ndims) + '\n')
            f.write('DimSize = ' + tuple_to_string(self.dim_size) + '\n')
            f.write('ElementType = ' + self.get_metaimage_type() + '\n')
            for key, value in self.attributes.items():
                f.write(key + ' = ' + value)
            f.write('ElementDataFile = ' + raw_filename)

        # Write raw file
        with open(self.base_path + raw_filename, 'wb') as f:
            f.write(np.vstack(self.data).tobytes())

