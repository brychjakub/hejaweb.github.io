from flask import Flask, send_from_directory
import os

app = Flask(__name__)
app.config['DEBUG'] = True

@app.route('/')
def my_home():
    """Hlavní stránka"""
    # Zkusíme najít index.html v aktuální složce
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Servírování statických souborů"""
    return send_from_directory('.', filename)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Servírování asset souborů"""
    return send_from_directory('assets', filename)

@app.route('/images/<path:filename>')
def serve_images(filename):
    """Servírování obrázků"""
    return send_from_directory('images', filename)

if __name__ == '__main__':
    print(f"Aktuální složka: {os.getcwd()}")
    print(f"Soubory ve složce: {os.listdir('.')}")
    app.run(debug=True, host='127.0.0.1', port=5000)