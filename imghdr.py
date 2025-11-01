# Заглушка для imghdr (удалён в Python 3.13)
# Совместимость с python-telegram-bot

def what(file, h=None):
    """Определяет тип изображения по первым байтам."""
    if h is None:
        if isinstance(file, str):
            with open(file, 'rb') as f:
                h = f.read(32)
        else:
            h = file.read(32)
            file.seek(0)

    # JPEG
    if h.startswith(b'\xff\xd8\xff'):
        return 'jpeg'
    # PNG
    if h.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    # GIF
    if h.startswith(b'GIF87a') or h.startswith(b'GIF89a'):
        return 'gif'
    # WebP
    if h[8:12] == b'WEBP':
        return 'webp'
    # BMP
    if h.startswith(b'BM'):
        return 'bmp'
    # TIFF
    if h.startswith(b'MM\x00\x2b') or h.startswith(b'II\x2a\x00'):
        return 'tiff'

    return None

# Для совместимости
def test_jpeg(h, f): return h[:3] == b'\xff\xd8\xff'
def test_png(h, f): return h.startswith(b'\x89PNG\r\n\x1a\n')
def test_gif(h, f): return h.startswith((b'GIF87a', b'GIF89a'))
