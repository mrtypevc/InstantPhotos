import os
import io
import requests
from flask import Flask, render_template, request, send_file, jsonify, session, redirect, url_for
from PIL import Image, ImageDraw
from dotenv import load_dotenv
import functools
try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'passport_photo_pro_secret_key_change_me')
APP_PASSWORD = os.getenv('APP_PASSWORD', '1234')

# Limit upload size to 16MB to save RAM
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == APP_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Ghalat Password! Fir se koshish karein.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))

# Configure Cloudinary
if CLOUDINARY_AVAILABLE and os.getenv('CLOUDINARY_CLOUD_NAME'):
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET'),
        secure=True
    )
else:
    CLOUDINARY_AVAILABLE = False

REMOVE_BG_API_KEY = os.getenv('REMOVE_BG_API_KEY')

# A4 dimensions at 300 DPI
A4_WIDTH = 2480
A4_HEIGHT = 3508

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
@login_required
def process():
    try:
        # Get settings
        width = int(request.form.get('width', 400))
        height = int(request.form.get('height', 400))
        spacing = int(request.form.get('spacing', 25))
        border_size = int(request.form.get('border', 2))
        bg_color = request.form.get('bg_color', '#ffffff')
        skip_ai = request.form.get('skip_ai') == 'true'

        processed_images = []
        
        # Process each uploaded image
        image_index = 0
        while f'image_{image_index}' in request.files:
            file = request.files[f'image_{image_index}']
            copies = int(request.form.get(f'copies_{image_index}', 1))
            
            if file:
                # Open with PIL immediately and resize to a manageable size to save RAM
                with Image.open(file) as raw_img:
                    # Convert to RGBA and thumbnail to max 1000px before processing
                    raw_img.thumbnail((1000, 1000))
                    img_io = io.BytesIO()
                    raw_img.save(img_io, format='PNG')
                    img_data = img_io.getvalue()

                
                # 1. AI Background Removal (remove.bg)
                if not skip_ai and REMOVE_BG_API_KEY and REMOVE_BG_API_KEY != 'your_remove_bg_api_key_here':
                    try:
                        response = requests.post(
                            'https://api.remove.bg/v1.0/removebg',
                            files={'image_file': img_data},
                            data={'size': 'auto', 'bg_color': bg_color.lstrip('#')},
                            headers={'X-Api-Key': REMOVE_BG_API_KEY},
                            timeout=5
                        )
                        if response.status_code == 200:
                            img_data = response.content
                    except: pass
                
                # 2. AI Image Enhancement (Cloudinary)
                if not skip_ai and CLOUDINARY_AVAILABLE:
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
                        img = Image.open(io.BytesIO(img_data)).convert("RGBA")
                        img = img.resize((width, height), Image.LANCZOS)
                else:
                    # Fallback to standard resize
                    img = Image.open(io.BytesIO(img_data)).convert("RGBA")
                    img = img.resize((width, height), Image.LANCZOS)

                # ALWAYS apply background color to handle transparency from remove.bg or original
                if bg_color:
                    # Ensure the image is in RGBA to have an alpha channel for masking
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    
                    # Ensure bg_color is applied under the image
                    new_img = Image.new("RGBA", img.size, bg_color)
                    # Paste the image onto the background
                    new_img.paste(img, (0, 0), mask=img.split()[3])
                    img.close()
                    img = new_img

                # Add border
                if border_size > 0:
                    bordered_img = Image.new('RGBA', (width + 2*border_size, height + 2*border_size), 'black')
                    bordered_img.paste(img, (border_size, border_size), img)
                    img.close()
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
        pages[0].save(pdf_buffer, format='PDF', save_all=True, append_images=pages[1:], optimize=True)
        
        # Cleanup
        for img in processed_images:
            img.close()
        for page in pages:
            page.close()
            
        pdf_buffer.seek(0)
        
        return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name='passport_photos.pdf')

    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
