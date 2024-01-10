from marshmallow import ValidationError
from marshmallow.fields import Field
from traceback import print_exc
from werkzeug.datastructures import FileStorage
from openpyxl import load_workbook
from zipfile import BadZipFile
from PIL import Image, UnidentifiedImageError
from pikepdf import Pdf, PasswordError, PdfError


class ExcelFile(Field):
    EXCEL_MIME = [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]

    def _deserialize(self, value, attr, data, **kwargs) -> FileStorage:
        try:
            if not isinstance(value, FileStorage):
                raise ValidationError("Server gagal melakukan pengecekan!")
            # validasi Content-Type
            if value.content_type not in ExcelFile.EXCEL_MIME:
                raise ValidationError(
                    "Maaf, hanya file excel yang boleh diupload!"
                )

            # coba buka file excel, jika gagal maka dinyatakan tidak valid
            wb = load_workbook(value)

            # coba baca properties dan sheet name, jika gagal maka dianggap tidak valid
            wb.properties
            wb.get_sheet_names()
            wb.close()

            return value
        except BadZipFile:
            raise ValidationError("File excel yang anda upload tidak valid!")
        except ValidationError as e:
            raise ValidationError(message=e.messages)
        except Exception:
            print_exc()
            raise ValidationError(
                "Server gagal melaukan validasi pada file excel yang anda upload!"
            )

class ImageFile(Field):
    ALLOWED_IMAGE_FORMAT = ["jpg", "jpeg", "png"]

    def _deserialize(self, value, attr, data, **kwargs) -> FileStorage:
        try:
            if not isinstance(value, FileStorage):
                raise ValidationError("Server gagal melakukan pengecekan!")

            # hanya Content-Type tipe image dan format yang ada pada constant ALLOWED_IMAGE_FORMAT yang di-ijinkan
            contentType = value.content_type.split("/")[1]
            if contentType not in ImageFile.ALLOWED_IMAGE_FORMAT:
                raise ValidationError(
                    f"Maaf, hanya gambar dengan format {ImageFile.ALLOWED_IMAGE_FORMAT} yang boleh diupload!"
                )

            # kita coba buka gambar untuk memastikan file benar-benar gambar
            # langkah ini juga mencegah dari serangan "decompression bombs"
            img = Image.open(value)

            # Content-Type dan extensi file masih bisa ditembus, contoh: file 'img.png', tapi ternyata file .gif
            # jadi kita baca format gambar-nya langsung untuk memastikan
            if img.format.lower() not in ImageFile.ALLOWED_IMAGE_FORMAT:
                raise ValidationError(
                    f"Maaf, hanya gambar dengan tipe {ImageFile.ALLOWED_IMAGE_FORMAT} yang boleh diupload, bukan {img.format}"
                )

            # coba baca attr mode, size, dll. Jika gagal maka file gambar tidak valid
            img.mode
            img.size
            img.palette
            img.info

            return value
        except (FileNotFoundError, UnidentifiedImageError, ValueError, TypeError):
            raise ValidationError("File gambar yang anda upload tidak valid!")
        except ValidationError as e:
            # just echoing error
            raise ValidationError(message=e.messages)
        except Exception:
            print_exc()
            raise ValidationError(
                "Server gagal melakukan validasi pada file gambar yang anda upload!"
            )

class PdfFile(Field):
    # TODO: buat validasi untuk pdf yang diberi password

    def _deserialize(self, value, attr, data, **kwargs) -> FileStorage:
        if not isinstance(value, FileStorage):
            raise ValidationError("Server gagal melakukan pengecekan!")

        try:
            # Content-Type wajib bertipe 'application/pdf'
            if value.content_type != "application/pdf":
                raise ValidationError(
                    "Maaf, hanya file pdf yang boleh diupload!"
                )

            # Content-Type masih bisa dimanipulasi, sehingga kita coba buka file pdf untuk memastikan
            pdf = Pdf.open(value)
            # Check if PDF is syntactically well-formed.
            if pdf.check():
                print("hasil pdf.check():", pdf.check())
                raise ValidationError("File pdf yang anda upload tidak valid!")

            return value
        except (PasswordError, PdfError, TypeError, FileNotFoundError):
            # jika file pdf gagal untuk dibaca, maka dianggap tidak valid
            raise ValidationError("File pdf yang anda upload tidak valid!")
        except ValidationError as e:
            # just echoing error
            raise ValidationError(message=e.messages)
        except Exception:
            print_exc()
            raise ValidationError(
                "Server gagal melakukan validasi pada file pdf yang anda upload!"
            )