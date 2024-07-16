import os
import img2pdf
import requests
from io import BytesIO
from flask import Flask, request, jsonify, send_file
from threading import Timer

app = Flask(__name__)

def fetch_image_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        return BytesIO(response.content)
    else:
        raise Exception(f"Failed to download image: {url}, status code: {response.status_code}")

def delete_file(filepath):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            app.logger.info(f"File {filepath} deleted successfully.")
    except Exception as e:
        app.logger.error(f"Error deleting file {filepath}: {e}")

@app.route('/convert', methods=['POST'])
def convert_to_pdf():
    try:
        data = request.json
        image_url = data.get('image_url')
        filename = data.get('filename', 'output')  # デフォルトファイル名は 'output'
        
        if not image_url:
            return jsonify({'error': 'Image URL is required'}), 400

        image_stream = fetch_image_from_url(image_url)
        pdf_bytes = img2pdf.convert([image_stream])

        tmp_dir = os.path.join(os.getcwd(), "tmp")
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        pdf_filename = os.path.join(tmp_dir, f"{filename}.pdf")
        with open(pdf_filename, "wb") as f:
            f.write(pdf_bytes)

        # 60秒後にファイルを削除
        t = Timer(60, delete_file, args=[pdf_filename])
        t.start()

        return jsonify({'pdf_url': f'http://127.0.0.1:5000/download/tmp/{filename}.pdf'})

    except Exception as e:
        app.logger.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/tmp/<filename>', methods=['GET'])
def download_file(filename):
    return send_file(os.path.join(os.getcwd(), "tmp", filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
