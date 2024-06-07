from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import db_init
import io
from pydub import AudioSegment
import speech_recognition as sr
import sqlite3
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db_init.create_table()

def get_db_connection():
    conn = sqlite3.connect('upload_history.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template('index.html')


@app.route("/upload_page", methods=["GET", "POST"])
def upload_page():
    transcript = ""
    if request.method == "POST":
        print("FORM DATA RECEIVED")

        if "file" not in request.files:
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)

        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            audio = AudioSegment.from_file(filepath, format="mp3")
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            wav_io.seek(0)

            recognizer = sr.Recognizer()
            audioFile = sr.AudioFile(wav_io)
            with audioFile as source:
                data = recognizer.record(source)
            transcript = recognizer.recognize_google(data, key=None)

            conn = get_db_connection()
            conn.execute(
                'INSERT INTO uploads (filename, transcript, timestamp, filepath) VALUES (?, ?, ?, ?)',
                (file.filename, transcript, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), filepath)
            )
            conn.commit()
            conn.close()

    return render_template('upload_page.html', transcript=transcript)

@app.route("/history")
def history():
    conn = get_db_connection()
    uploads = conn.execute('SELECT * FROM uploads').fetchall()
    conn.close()
    return render_template('history.html', uploads=uploads)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/rec_page')
def rec_page():
    return render_template('rec_page.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        audio_data = request.files['audio_data']
        audio_content = audio_data.read()

        with io.BytesIO(audio_content) as temp_audio_file:
            temp_audio_file.seek(0)
            audio = AudioSegment.from_file(temp_audio_file, format="webm")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_audio_path = os.path.join(UPLOAD_FOLDER, f'audio_{timestamp}.wav')

            audio.export(final_audio_path, format="wav")

            recognizer = sr.Recognizer()
            with sr.AudioFile(final_audio_path) as source:
                audio = recognizer.record(source)
                transcription = recognizer.recognize_google(audio)

            transcription_path = os.path.join(UPLOAD_FOLDER, f'transcription_{timestamp}.txt')
            with open(transcription_path, 'w') as f:
                f.write(transcription)

            conn = get_db_connection()
            conn.execute(
                'INSERT INTO uploads (filename, transcript, timestamp, filepath) VALUES (?, ?, ?, ?)',
                (f'audio_{timestamp}.wav', transcription, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), final_audio_path)
            )
            conn.commit()
            conn.close()

            return transcription

    except Exception as e:
        return f'Error: {str(e)}'

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
