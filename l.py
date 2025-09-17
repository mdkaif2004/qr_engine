import qrcode

# 1. Define your vCard text
vcard = """BEGIN:VCARD
VERSION:3.0
N:Doe;John;;;
FN:John Doe
TEL;TYPE=CELL:+15551234567
EMAIL:john@example.com
END:VCARD
"""

# 2. Create a QR code from the vCard
qr = qrcode.QRCode(
    version=1,  # controls size (1 = smallest)
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)
qr.add_data(vcard)
qr.make(fit=True)

# 3. Generate and save QR code image
img = qr.make_image(fill_color="black", back_color="white")
img.save("vcard_qr.png")

print("✅ QR code saved as vcard_qr.png")
