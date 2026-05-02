import re
import requests
from flask import Flask, request, jsonify, send_from_directory
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

app = Flask(__name__, static_folder=".")


def extract_video_id(url):
    patterns = [
        r"(?:v=)([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"shorts/([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/video-info")
def video_info():
    url = request.args.get("url", "").strip()
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid URL"}), 400
    try:
        oembed = requests.get(
            f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json",
            timeout=5
        ).json()
        return jsonify({
            "title": oembed.get("title", "Unknown title"),
            "channel": oembed.get("author_name", ""),
            "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        })
    except Exception:
        return jsonify({"error": "Could not load video info"}), 500


@app.route("/transcript")
def transcript():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "Please provide a YouTube URL."}), 400

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Could not find a valid YouTube video ID in that URL."}), 400

    try:
        api = YouTubeTranscriptApi()
        entries = api.fetch(video_id)
        lines = [snippet.text for snippet in entries]
        return jsonify({"transcript": lines})
    except TranscriptsDisabled:
        return jsonify({"error": "Transcripts are disabled for this video."}), 404
    except NoTranscriptFound:
        return jsonify({"error": "No transcript found for this video."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/translate")
def translate():
    text = request.args.get("text", "").strip()
    src  = request.args.get("src", "en")
    tgt  = request.args.get("tgt", "es")
    if not text:
        return jsonify({"error": "No text provided"}), 400
    try:
        resp = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": f"{src}|{tgt}"},
            timeout=8
        ).json()
        translated = resp["responseData"]["translatedText"]
        return jsonify({"translated": translated})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=8080)
