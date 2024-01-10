from marshmallow import ValidationError


def file_size(min_kb: int = 0, max_kb: int = 1024):
    '''
        Untuk validasi ukuran file yg di-upload (dalam kb)
    '''

    def size(file):
        file.seek(0, 2)
        file_size = file.tell() / 1024

        if file_size < min_kb:
            raise ValidationError(f"Ukuran file minimal adalah: {min_kb}")

        if file_size > max_kb:
            raise ValidationError(f"Ukuran file tidak boleh lebih dari {max_kb} kb!")

    return size
