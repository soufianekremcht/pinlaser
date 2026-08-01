import struct
import sys

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImage

ICON_SIZES = [16, 24, 32, 48, 64, 128, 256]


def load_square_png(path, size):
    image = QImage(path)
    if image.isNull():
        raise RuntimeError(f"could not load image: {path}")
    scaled = image.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    return scaled.convertToFormat(QImage.Format.Format_ARGB32)


def png_bytes(image):
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise RuntimeError("could not encode PNG")
    return bytes(data)


def write_ico(images, out_path):
    count = len(images)
    header = struct.pack("<HHH", 0, 1, count)
    entries = b""
    payload = b""
    offset = 6 + 16 * count
    for size, image in images:
        data = png_bytes(image)
        dim = size if size < 256 else 0
        entries += struct.pack(
            "<BBBBHHII",
            dim,
            dim,
            0,
            0,
            1,
            32,
            len(data),
            offset,
        )
        payload += data
        offset += len(data)
    with open(out_path, "wb") as fh:
        fh.write(header + entries + payload)


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else "assets/app_icon_pin-laser.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "packaging/pinlaser.ico"
    app = QGuiApplication(sys.argv)
    images = [(size, load_square_png(source, size)) for size in ICON_SIZES]
    write_ico(images, out)
    print(f"wrote {out} ({len(images)} sizes)")


if __name__ == "__main__":
    main()
