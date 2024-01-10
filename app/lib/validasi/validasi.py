from marshmallow import ValidationError, INCLUDE
from marshmallow.fields import Field
from marshmallow.schema import Schema
from werkzeug.datastructures import FileStorage
from itsdangerous.exc import BadSignature
from urllib.parse import unquote
from .fields import ExcelFile
from .utils import FileTypeNotSupported, decodeValidationError, secureExcelFileName, secureImgFileName, securePdfFileName, serializer


class Validasi:
    SUPPORTED_FILES = [
        "image/png",
        "image/jpg",
        "image/jpeg",
        "application/pdf",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]

    def __secureFileName(self, file: FileStorage) -> FileStorage:
        """
        ini merupakan driver method untuk mengamankan nama file dari 'path traversal'. Untuk alasan keamanan, pembuatan extensi file (.pdf, .png, dll)
        dibuat secara hardcode. Contoh: "file.php.pdf" -> kita ambil nama file-nya aja -> "file" -> kemudian tambahkan extensi sendiri ".pdf" -> "file.pdf".
        Sehingga kita pakai if else di fungsi ini sesuai dengan jenis file yang disupport berdasarkan kesepakatan bersama.
        """
        if file.content_type == "application/pdf":
            return securePdfFileName(file)
        elif file.content_type.split("/")[0] == "image":
            return secureImgFileName(file)
        elif file.content_type in ExcelFile.EXCEL_MIME:
            return secureExcelFileName(file)

    def __str__(self) -> str:
        return f"<HasilValidasi: Error={self.error}, Message={self.list_message}>"

    def __init__(
        self, schema: dict, data: dict, unknown: bool = False, unsupported: bool = False, verbose: bool = False
    ) -> None:
        self.error = True
        self.list_message = [
            {
                'key': None,
                'value': None,
                'message': 'Terjadi kesalahan internal!'
            }
        ]
        self.unknown = INCLUDE if unknown else None

        '''
            Deteksi apakah data berasal dari DataTable?, jika iya maka:
                - unknown = INCLUDE
                - Bagian verbose tidak perlu print data yang berasal dari DataTable
        '''
        is_dataTable = "columns[0][data]" in data.keys()

        if is_dataTable:
            self.unknown = INCLUDE

        try:
            dataKotor = data

            # pre-processing data
            dataBersih = {}
            for k, v in dataKotor.items():
                self.__tempKey, self.__tempValue = k, v
                '''
                    terkadang kita kirim data ke FE kemudian kita kirim lagi datanya ke BE,
                    jadi data harus ditandatangani untuk mendeteksi perubahan. proses ini pakai library itsdangerous.
                    Contoh data: '"KZ01"$.$j2KKEBkIhr8xN3n0w6Rwv3GvJbE'
                '''

                # Data yg perlu validasi signed, pada schema fieldnya wajib ada metadata SIGNED ({'signed': True}),
                # contoh: nik = Str(required=True, metadata={'signed': True}, ...)
                signed = schema.get(k, Field()).metadata.get('signed', False)
                if signed:
                    # lakukan validasi itsdangerous,
                    # jika tidak valid maka akan raise BadSignature
                    payload = serializer.loads(unquote(v))

                    # jika valid, masukan payload ke dataBersih
                    self.__tempKey = payload
                    dataBersih[k] = payload
                elif isinstance(v, FileStorage) and not v.filename:
                    # jika user tidak upload file maka akan menjadi <FileStorage: '' ('application/octet-stream')>
                    # yang mana tidak valid karena Content-Type tidak terdaftar, jadi kita hapus file yang filename-nya kosong
                    pass
                else:
                    dataBersih[k] = v

            """
            Jika flag unsupported False (default) maka jika ada data dengan tipe FileStorage dan
            Content-Type-nya tidak terdaftar dalam constant SUPPORTED_FILES akan raise error.
            """
            if not unsupported:
                for k, v in dataBersih.items():
                    self.__tempKey, self.__tempValue = k, v
                    if isinstance(v, FileStorage) and v.content_type not in Validasi.SUPPORTED_FILES:
                        raise FileTypeNotSupported(v.content_type)

            # setelah data bersih maka lanjutkan pengecekan data
            schema = Schema.from_dict(schema)
            schema().load(dataBersih, unknown=self.unknown)

            # jika tidak ada error, maka data dinyatakan valid
            self.data = dataBersih
            self.error = False
            self.list_message = "OK"

            # jika verbose True maka print semua data ke terminal
            if verbose is True:
                # Bagian verbose tidak perlu print data yang berasal dari DataTable
                if is_dataTable:
                    print_data = {
                        k: v
                        for k, v in dataBersih.items()
                        if not k.startswith("columns[")
                        and not k.startswith("search[")
                    }
                    del print_data['draw']
                    del print_data['start']
                    del print_data['length']
                    del print_data['_']
                else:
                    print_data = dataBersih

                for k, v in print_data.items():
                    print(f"{k}: {v}")
        except ValidationError as e:
            # jika terjadi ValidationError, maka data dinyatakan tidak valid
            self.error = True
            self.list_message = decodeValidationError(e, dataKotor)
        except FileTypeNotSupported as e:
            self.error = True
            self.list_message = [{
                'key': self.__tempKey,
                'value': self.__tempValue,
                'message': str(e)
            }]
            print(str(self.list_message[0]))
        except BadSignature as e:
            payload = e.payload or str(self.__tempValue).encode('utf-8')
            self.error = True
            self.list_message = [{
                'key': self.__tempKey,
                'value': payload.decode('utf-8'),
                'message': f'''Tanda tangan tidak valid!'''
            }]
            print(str(self.list_message[0]))

    def getData(self) -> dict:
        # jika validasi sukses, maka wajib ambil data pakai method ini
        if self.error:
            return {}

        """
        walaupun semua data sudah dianggap valid, namun kita masih perlu untuk merubah nama
        file ulang agar terhindar dari 'path transversal', sehingga kita loop self.data,
        kemudian amankan nama file pakai method self.__secureFileName() jika data-nya bertipe FileStorage (file uplaod)
        """
        return {
            k: self.__secureFileName(v) if isinstance(v, FileStorage) else v
            for k, v in self.data.items()
        }
