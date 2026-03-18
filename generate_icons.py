"""Generate PWA icons for Cold Email Generator."""
import os

def generate_icons():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow not available, creating placeholder icons")
        create_placeholder_icons()
        return

    os.makedirs('static/icons', exist_ok=True)

    def draw_icon(size, maskable=False):
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background gradient (blue to purple)
        for y in range(size):
            ratio = y / size
            r = int(37 + (124 - 37) * ratio)
            g = int(99 + (58 - 99) * ratio)
            b = int(235 + (237 - 235) * ratio)
            draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

        # Rounded rectangle background
        radius = size // 5 if maskable else size // 8
        draw.rounded_rectangle([0, 0, size-1, size-1], radius=radius, fill=None, outline=None)

        # Envelope body
        pad = size * 0.18
        env_left = int(pad)
        env_top = int(size * 0.32)
        env_right = int(size - pad)
        env_bottom = int(size * 0.72)

        # Envelope background
        draw.rectangle([env_left, env_top, env_right, env_bottom], fill=(255, 255, 255, 230), outline=(255, 255, 255, 200), width=2)

        # Envelope flap (V shape)
        mid_x = size // 2
        draw.polygon([
            (env_left, env_top),
            (mid_x, int(size * 0.52)),
            (env_right, env_top)
        ], fill=(200, 220, 255, 200))

        # AI sparkle - top right
        spark_x = int(size * 0.72)
        spark_y = int(size * 0.22)
        spark_r = int(size * 0.07)
        # Star sparkle
        for angle in range(0, 360, 45):
            import math
            rad = math.radians(angle)
            length = spark_r if angle % 90 == 0 else spark_r // 2
            x2 = int(spark_x + math.cos(rad) * length)
            y2 = int(spark_y + math.sin(rad) * length)
            draw.line([(spark_x, spark_y), (x2, y2)], fill=(255, 220, 100, 255), width=max(2, size // 80))

        draw.ellipse([spark_x-3, spark_y-3, spark_x+3, spark_y+3], fill=(255, 240, 150, 255))

        return img

    # Normal icon
    icon = draw_icon(512, maskable=False)
    icon.save('static/icons/icon-512.png', 'PNG')
    print("Generated icon-512.png")

    # Maskable icon (with safe zone padding ~10%)
    maskable = draw_icon(512, maskable=True)
    maskable.save('static/icons/icon-maskable-512.png', 'PNG')
    print("Generated icon-maskable-512.png")


def create_placeholder_icons():
    """Tiny valid PNG files as fallback."""
    import struct, zlib

    def make_png(color_hex):
        r = int(color_hex[1:3], 16)
        g = int(color_hex[3:5], 16)
        b = int(color_hex[5:7], 16)
        w = h = 64
        raw = b''
        for _ in range(h):
            raw += b'\x00' + bytes([r, g, b] * w)
        compressed = zlib.compress(raw)
        def chunk(tag, data):
            c = struct.pack('>I', len(data)) + tag + data
            crc = zlib.crc32(tag + data) & 0xffffffff
            return c + struct.pack('>I', crc)
        ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
        return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', compressed) + chunk(b'IEND', b'')

    with open('static/icons/icon-512.png', 'wb') as f:
        f.write(make_png('#2563eb'))
    with open('static/icons/icon-maskable-512.png', 'wb') as f:
        f.write(make_png('#7c3aed'))
    print("Created placeholder icons")


if __name__ == '__main__':
    generate_icons()
