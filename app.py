import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

from flask import Flask, request, render_template, jsonify
from googleapiclient.discovery import build
from textblob import TextBlob
import matplotlib.pyplot as plt
import io
import base64
import threading
import webbrowser

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Define themes and associated keywords
THEMES = {
    "quality": ["good", "bad", "excellent", "poor", "amazing"],
    "price": ["cheap", "expensive", "affordable", "costly"],
    "performance": ["fast", "slow", "lag", "smooth", "responsive"],
    "content": ["funny", "boring", "interesting", "educational"]
}

# Function to fetch YouTube comments
def get_youtube_comments(api_key, video_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.commentThreads().list(
        part='snippet',
        videoId=video_id,
        maxResults=100
    )
    response = request.execute()
    comments = []
    for item in response.get('items', []):
        comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
        comments.append(comment)
    return comments

# Function to analyze sentiment and detect themes
def analyze_sentiment_and_themes(comments):
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    theme_counts = {theme: 0 for theme in THEMES}
    labeled_comments = []

    for comment in comments:
        # Analyze sentiment
        analysis = TextBlob(comment)
        polarity = analysis.sentiment.polarity
        if polarity > 0:
            sentiment = "positive"
        elif polarity < 0:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        sentiment_counts[sentiment] += 1

        # Detect themes
        detected_themes = []
        for theme, keywords in THEMES.items():
            if any(keyword in comment.lower() for keyword in keywords):
                detected_themes.append(theme)
                theme_counts[theme] += 1

        labeled_comments.append({
            "comment": comment,
            "sentiment": sentiment,
            "themes": detected_themes
        })

    return sentiment_counts, theme_counts, labeled_comments

# Function to plot sentiments
def plot_sentiments(sentiment_counts):
    labels = sentiment_counts.keys()
    sizes = sentiment_counts.values()
    colors = ['#66b3ff', '#ffcc99', '#ff6666']
    
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140)
    plt.axis('equal')

    # Save pie chart to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode()

# Route to render home page
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle sentiment analysis
@app.route('/analyze', methods=['POST'])
def analyze():
    api_key = request.form['api_key']
    video_id = request.form['video_id']
    
    try:
        comments = get_youtube_comments(api_key, video_id)
        sentiment_counts, theme_counts, labeled_comments = analyze_sentiment_and_themes(comments)
        chart = plot_sentiments(sentiment_counts)

        # Debug: Print the size of the chart string
        print(f"Chart size (Base64): {len(chart)} characters")

        return jsonify({
            "chart": chart,
            "comments": labeled_comments,
            "themes": theme_counts
        })
    except Exception as e:
        return jsonify({"error": str(e)})

# Function to open the app in the default web browser
def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

# Main block to run the app
if __name__ == '__main__':
    threading.Timer(1, open_browser).start()
    app.run(debug=True)



