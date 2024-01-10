"""
    Modul compressFile develop by Candra (20 Mar 2023)
    Versi: 1.0 (24 Mar 2023)
"""


from werkzeug.datastructures import FileStorage
from PIL import Image
from io import BytesIO
from pikepdf import Pdf, PdfImage, Name


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def compressImage(file: FileStorage, quality: int = 47) -> FileStorage:
    file.seek(0, 2)
    print("raw_image:", sizeof_fmt(file.tell()))
    # load gambar ke PIL
    raw_image = Image.open(file)

    # hanya bisa compress gambar dengan format jpg, jpeg, png
    if raw_image.format not in {"JPG", "JPEG", "PNG"}:
        raise Exception("Hanya file PNG / JPG / JPEG yang didukung!")

    # compress gambar dan tampung ke variable compressed_image
    compressed_image = BytesIO()

    # untuk format PNG ubah ke mode "P" (8-bit pixels) agar compress lebih ganas
    # TODO: perlu dioptimasi pada palette agar warna gambar tetap bagus, saya pusing bikin palette-nya :)
    if raw_image.format == "PNG":
        raw_image = raw_image.quantize(method=2)
        raw_image.format = "PNG"

    # jika format JPG / JPEG maka quality ditentukan oleh kwargs 'quality' (1 ~ 95)
    # sedangkan format PNG ditentukan oleh kwargs 'compress_level' (0 ~ 9) atau kwargs 'optimize' jika True maka compress_level otomatis set ke 9
    raw_image.save(
        fp=compressed_image,
        format=raw_image.format,
        quality=quality,
        optimize=True
    )
    print("compressed_image:", sizeof_fmt(compressed_image.tell()))
    raw_image.close()

    # replace gambar ori ke gambar yang sudah di comppress
    compressed_image.seek(0)
    file.stream = compressed_image
    return file


def compressPdf(file: FileStorage, quality: int = 30) -> FileStorage:
    file.seek(0, 2)
    print("raw_pdf:", sizeof_fmt(file.tell()))

    # load pdf, then loop through pages to compress all image
    raw_pdf = Pdf.open(file)
    for page in raw_pdf.pages:
        for raw_image in page.images:
            # load image
            raw_image = page.images.get(raw_image)
            pillow_image = PdfImage(raw_image).as_pil_image()
            compressed_image = BytesIO()

            # compress image
            pillow_image.save(
                fp=compressed_image,
                format=pillow_image.format,
                quality=quality,
                optimize=True,
            )

            # replace raw_image with compressed_image
            raw_image.write(
                compressed_image.getvalue(), filter=Name("/DCTDecode")
            )

            # close file to release memory
            compressed_image.close()
            pillow_image.close()

    # remove unecessary object to reduce pdf size
    raw_pdf.remove_unreferenced_resources()

    # write compressed_pdf
    compressed_pdf = BytesIO()
    raw_pdf.save(compressed_pdf)
    raw_pdf.close()
    print("compressed_pdf:", sizeof_fmt(compressed_pdf.tell()))

    # replace raw pdf with compressed pdf
    compressed_pdf.seek(0)
    file.stream = compressed_pdf
    return file
