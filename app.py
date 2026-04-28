import os
import io
import requests
from flask import Flask, render_template, request, send_file, jsonify
from PIL import Image, ImageDraw
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api

load_dotenv()

app = Flask(__name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

REMOVE_BG_API_KEY = os.getenv('REMOVE_BG_API_KEY')

# A4 dimensions at 300 DPI
A4_WIDTH = 2480
A4_HEIGHT = 3508

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        # Get settings
        width = int(request.form.get('width', 400))
        height = int(request.form.get('height', 400))
        spacing = int(request.form.get('spacing', 25))
        border_size = int(request.form.get('border', 2))

        processed_images = []

        # Process each uploaded image
        image_index = 0
        while f'image_{image_index}' in request.files:
            file = request.files[f'image_{image_index}']
            copies = int(request.form.get(f'copies_{image_index}', 1))

            if file:
                img_data = file.read()

                # 1. AI Background Removal (remove.bg)
                if REMOVE_BG_API_KEY and REMOVE_BG_API_KEY != 'your_remove_bg_api_key_here':
                    response = requests.post(
                        'https://api.remove.bg/v1.0/removebg',
                        files={'image_file': img_data},
                        data={'size': 'auto'},
                        headers={'X-Api-Key': REMOVE_BG_API_KEY},
                    )

                    if response.status_code == 200:
                        img_data = response.content
                    else:
                        print(f"Remove.bg error: {response.text}")

                # 2. AI Image Enhancement (Cloudinary)
                if os.getenv('CLOUDINARY_CLOUD_NAME') and os.getenv('CLOUDINARY_CLOUD_NAME') != 'your_cloud_name':
                    try:
                        upload_result = cloudinary.uploader.upload(
                            img_data,
                            transformation=[
                                {"effect": "gen_restore"},
                                {"width": width, "height": height, "crop": "fill"}
                            ]
                        )
                        enhanced_url = upload_result['secure_url']
                        enhanced_img_data = requests.get(enhanced_url).content
                        img = Image.open(io.BytesIO(enhanced_img_data)).convert("RGBA")
                    except Exception as e:
                        print(f"Cloudinary error: {e}")
                        img = Image.open(io.BytesIO(img_data)).convert("RGBA")
                        img = img.resize((width, height), Image.LANCZOS)
                else:
                    img = Image.open(io.BytesIO(img_data)).convert("RGBA")
                    img = img.resize((width, height), Image.LANCZOS)

                # Add border if needed
                if border_size > 0:
                    bordered_img = Image.new('RGBA', (width + 2*border_size, height + 2*border_size), 'black')
                    bordered_img.paste(img, (border_size, border_size), img)
                    img = bordered_img

                processed_images.extend([img] * copies)

            image_index += 1

        if not processed_images:
            return "No images processed", 400

        # Generate PDF Pages
        pages = []
        current_page = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), 'white')
        draw = ImageDraw.Draw(current_page)

        x_margin = 100
        y_margin = 100
        curr_x = x_margin
        curr_y = y_margin

        img_w, img_h = processed_images[0].size

        for img in processed_images:
            if curr_x + img_w > A4_WIDTH - x_margin:
                curr_x = x_margin
                curr_y += img_h + spacing

            if curr_y + img_h > A4_HEIGHT - y_margin:
                pages.append(current_page)
                current_page = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), 'white')
                curr_x = x_margin
                curr_y = y_margin

            current_page.paste(img, (curr_x, curr_y), img if img.mode == 'RGBA' else None)
            curr_x += img_w + spacing

        pages.append(current_page)

        # Save to PDF
        pdf_buffer = io.BytesIO()
        pages[0].save(pdf_buffer, format='PDF', save_all=True, append_images=pages[1:])
        pdf_buffer.seek(0)

        return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name='passport_photos.pdf')

    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
