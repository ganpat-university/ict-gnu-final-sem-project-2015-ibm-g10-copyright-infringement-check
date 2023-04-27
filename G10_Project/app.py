import os
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from image_comparison import compare_image
from video_comparison import compare_video
from video_comparison import videos_folder
from image_comparison import images_folder
import shutil
from waitress import serve

app = Flask(__name__)
app.secret_key = "supersecretkey"
comparison_progress = 0

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'avi'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        global comparison_progress
        comparison_progress = 0

        file = request.files['file']
        if not file or not allowed_file(file.filename):
            flash("Please upload a valid image or video file.")
            return redirect(request.url)

        name = request.form['name']
        file_path = os.path.join("uploads", secure_filename(name + "_" + file.filename.rsplit('.', 1)[0].replace(" ", "_") + "." + file.filename.rsplit('.', 1)[1]))
        file.save(file_path)

        file_type = "undefined"
        result = None
        if file.filename.lower().endswith(('.jpeg', '.jpg', '.png')):
            file_type = "image"
            result = compare_image(file_path)
        elif file.filename.lower().endswith(('.mp4', '.avi')):
            file_type = "video"
            result = compare_video(file_path, progress_callback=lambda p: set_progress(p))

        # os.remove(file_path)

        if result:
            if result["unique"]:
                flash("No match found. This is a unique file.")
                if file_type == "image":
                    shutil.copy2(file_path, images_folder)
                elif file_type == "video":
                    shutil.copy2(file_path, videos_folder)
            else:
                flash(f"Match found! \nFile name: {result['filename']}. Similarity: {result['similarity']:.2f}%")

        os.remove(file_path)

    return render_template("index.html")

def set_progress(progress):
    global comparison_progress
    comparison_progress = progress

@app.route('/progress')
def progress():
    return jsonify(progress=comparison_progress)

if __name__ == "__main__":
    # app.run(debug=True, host="192.168.1.114")
    serve(app, host="192.168.1.114", port=8080, threads=10)
