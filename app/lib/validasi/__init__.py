"""
    Modul validasi Develop by Candra (13 Mar 2023)
    Versi: 2.1 (07 September 2023)

    NOTE: Pengecekan file kurang aman jika hanya mengecek berdasarkan 'magic numbers' seperti yang dilakukan modul berikut:
    imghdr, filetype, puremagic, python-magic. Sehingga pada modul ini saya tidak menggunakannya
"""
from .validasi import Validasi
from .fields import ExcelFile, ImageFile, PdfFile
from .utils import decodeValidationError
from .validate import file_size

__all__ = [
    "Validasi",
    "ExcelFile",
    "ImageFile",
    "PdfFile",
    "decodeValidationError",
    "file_size"
]
