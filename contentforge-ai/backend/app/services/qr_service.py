import base64
import io
import logging
from typing import Optional
import qrcode

logger = logging.getLogger(__name__)


def generate_qr_code_png_bytes(data: str) -> bytes:
    """Generate a PNG byte stream containing a QR code for the provided data URL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_qr_code_base64(data: str) -> str:
    """Generate a base64 encoded PNG data URI for a QR code."""
    png_bytes = generate_qr_code_png_bytes(data)
    b64_str = base64.b64encode(png_bytes).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"
