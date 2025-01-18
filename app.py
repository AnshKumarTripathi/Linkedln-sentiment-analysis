from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from textblob import TextBlob
from scrape_content import LinkedInScraper

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    scraper = LinkedInScraper()
    scraper.run_scraper()
    
    df = pd.read_csv('linkedin_posts.csv')
    
    def analyze_sentiment(content):
        analysis = TextBlob(content)
        return 'positive' if analysis.sentiment.polarity > 0 else 'negative' if analysis.sentiment.polarity < 0 else 'neutral'
    
    df['sentiment'] = df['content'].apply(analyze_sentiment)
    
    posts = df.to_dict(orient='records')
    
    return render_template('index.html', posts=posts)

if __name__ == '__main__':
    app.run(debug=True)
