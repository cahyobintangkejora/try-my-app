from itsdangerous.serializer import Serializer
from marshmallow import ValidationError
from typing import List, Dict
from werkzeug.datastructures import FileStorage
from PIL import Image
from werkzeug.utils import secure_filename
import inspect
from datetime import datetime
from app import serializer

'''
    Wajib setup serializer, jika didapat dari hasil import,
    maka dicomment aja.
'''
# serializer = Serializer('ini sk', signer_kwargs={'sep': '$.$'})



class FileTypeNotSupported(Exception):
    """
    Raise ketika data dengan tipe FileStorage yang hendak divalidasi Content-Type-nya tidak tercantum dalam constant Validasi.SUPPORTED_FILES
    """

    def __init__(self, content_type: str) -> None:
        self.content_type = content_type

    def __str__(self) -> str:
        return f"Untuk alasan keamanan file dengan tipe '{self.content_type}' belum didukung, sehingga dilarang untuk diupload!"


def decodeValidationError(e: ValidationError, dataKotor: dict) -> List[Dict]:
    """
    fungsi untuk membuat pesan error ketika data yang dikirim tidak valid. Ada 2 argumen:
        1. e: merupakan instance dari marshmallow.ValidationError, didapat ketika data yang dicek tidak valid
        2. dataKotor: merupakan raw data yang dikirim oleh user
    """

    listError = []
    # e.message adalah dict dari seluruh value yang error -> {'divisi': 'Must be one of: it, finance'}
    # kita loop untuk membentuk pesan error yang rapi
    for k, v in e.messages.items():
        # compose pesan error. contoh: {'key': 'divisi', 'value': 'dev', message: 'Must be one of: it, finance'}
        message = {"key": k, "value": str(dataKotor.get(k)), "message": v[0]}
        listError.append(message)

    # get caller
    caller_frame = inspect.currentframe().f_back.f_back
    caller_name = caller_frame.f_code.co_name
    caller_filename = caller_frame.f_code.co_filename
    caller_lineno = caller_frame.f_lineno
    caller_info = f'File "{caller_filename}", line {caller_lineno}, in {caller_name}'

    # construct error info
    time = datetime.now().strftime("[%d-%m-%Y %H:%M:%S]")
    error_header = f"{time} [ERROR] ValidationError on {caller_info}:\n"
    error_message = "\n".join(str(i) for i in listError)

    # kita print dan juga kita return
    print(error_header + error_message)
    return listError


def decodeFileName(file: FileStorage) -> str:
    # Decode filename untuk menghindari path transversal.
    secureFileName = secure_filename(file.filename).strip()

    """
    Ambil nama file saja tanpa extension, contoh: "file.php.pdf" ->  "file"
    Tujuan-nya biar extensi file harcode manual sesuai tipe file yang diijinkan
    """
    filenameWithoutExt = secureFileName.split(".")[0]

    if not filenameWithoutExt:
        raise ValidationError("Nama file tidak di-ijinkan!")

    return filenameWithoutExt


def securePdfFileName(file: FileStorage) -> FileStorage:
    filename = decodeFileName(file) + ".pdf"
    # Ubah nama file dengan nama yang sudah aman / secure. Kemudian return
    file.filename = filename
    return file


def secureImgFileName(file: FileStorage) -> FileStorage:
    # output extensi = 'jpg, png, jpeg, ...'
    extensi = Image.open(file).format.lower()
    filename = decodeFileName(file) + "." + extensi

    # ubah nama file dengan nama yang sudah aman / secure. Kemudian return
    file.filename = filename
    return file


def secureExcelFileName(file: FileStorage) -> FileStorage:
    filename = decodeFileName(file)
    if file.content_type == "application/vnd.ms-excel":
        extension = ".xls"
    else:
        extension = ".xlsx"

    file.filename = filename + extension
    return file
