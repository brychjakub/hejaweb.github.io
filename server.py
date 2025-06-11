from flask import Flask, render_template, send_from_directory
import os

# Vytvoření Flask aplikace
app = Flask(__name__)

# Nastavení pro PythonAnywhere
app.config['DEBUG'] = False

@app.route('/')
def index():
    """Hlavní stránka"""
    return send_from_directory('hejaWeb', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Servírování statických souborů"""
    return send_from_directory('hejaWeb', filename)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Servírování asset souborů"""
    return send_from_directory('hejaWeb/assets', filename)

@app.route('/images/<path:filename>')
def serve_images(filename):
    """Servírování obrázků"""
    return send_from_directory('hejaWeb/images', filename)

if __name__ == '__main__':
    app.run(debug=True)
