import pandas as pd
from textblob import TextBlob
import matplotlib.pyplot as plt

df = pd.read_csv('linkedin_posts.csv')

def analyze_sentiment(content):
    analysis = TextBlob(content)
    return analysis.sentiment.polarity

df['sentiment'] = df['content'].apply(analyze_sentiment)

df['sentiment_category'] = df['sentiment'].apply(lambda x: 'positive' if x > 0 else 'negative' if x < 0 else 'neutral')

df.to_csv('linkedin_posts_sentiment.csv', index=False)

sentiment_summary = df['sentiment_category'].value_counts()
print("\nSentiment Analysis Summary:")
print(sentiment_summary)

plt.figure(figsize=(10, 6))
sentiment_summary.plot(kind='bar', color=['green', 'red', 'gray'])
plt.xlabel('Sentiment')
plt.ylabel('Number of Posts')
plt.title('Sentiment Analysis of LinkedIn Posts')
plt.show()
