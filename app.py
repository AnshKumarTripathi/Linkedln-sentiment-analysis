from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from textblob import TextBlob
from scrape_content import LinkedInScraper
import os
from threading import Thread

app = Flask(__name__)

def analyze_sentiment(content):
    try:
        analysis = TextBlob(str(content))
        polarity = analysis.sentiment.polarity
        
        if polarity > 0.2:
            sentiment = 'positive'
        elif polarity < -0.2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
            
        return {
            'sentiment': sentiment,
            'polarity': round(polarity, 2),
        }
    except Exception as e:
        return {'sentiment': 'error', 'polarity': 0}

def process_data(df):
    if df is None or df.empty:
        return None, None
        
    df['sentiment_analysis'] = df['content'].apply(analyze_sentiment)
    df['sentiment'] = df['sentiment_analysis'].apply(lambda x: x['sentiment'])
    df['polarity'] = df['sentiment_analysis'].apply(lambda x: x['polarity'])
    
    posts = df.to_dict(orient='records')
    
    stats = {
        'positive': len(df[df['sentiment'] == 'positive']),
        'negative': len(df[df['sentiment'] == 'negative']),
        'neutral': len(df[df['sentiment'] == 'neutral'])
    }
    
    return posts, stats

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze_feed', methods=['POST'])
def analyze_feed():
    try:
        scraper = LinkedInScraper()
        df = scraper.run_scraper(scrape_type='feed')
        posts, stats = process_data(df)
        
        if posts:
            return render_template('index.html', posts=posts, stats=stats)
        else:
            return render_template('index.html', error="No feed posts collected")
    except Exception as e:
        return render_template('index.html', error=f"Error analyzing feed: {str(e)}")

@app.route('/analyze_user_posts', methods=['POST'])
def analyze_user_posts():
    try:
        scraper = LinkedInScraper()
        df = scraper.run_scraper(scrape_type='user_posts')
        posts, stats = process_data(df)
        
        if posts:
            return render_template('index.html', posts=posts, stats=stats)
        else:
            return render_template('index.html', error="No user posts collected")
    except Exception as e:
        return render_template('index.html', error=f"Error analyzing user posts: {str(e)}")

@app.route('/analyze_messages', methods=['POST'])
def analyze_messages():
    try:
        scraper = LinkedInScraper()
        df = scraper.run_scraper(scrape_type='messages')
        posts, stats = process_data(df)
        
        if posts:
            return render_template('index.html', posts=posts, stats=stats)
        else:
            return render_template('index.html', error="No messages collected")
    except Exception as e:
        return render_template('index.html', error=f"Error analyzing messages: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)