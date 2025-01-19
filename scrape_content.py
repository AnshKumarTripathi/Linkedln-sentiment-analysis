from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

class LinkedInScraper:
    def __init__(self):
        self.driver = None
        load_dotenv()
        
    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-notifications')
        options.add_argument('--start-maximized')
        self.driver = webdriver.Chrome(options=options)
        
    def login(self):
        try:
            print("Attempting to login...")
            self.driver.get('https://www.linkedin.com/login')
            time.sleep(3)
            
            email = self.driver.find_element(By.ID, 'username')
            password = self.driver.find_element(By.ID, 'password')
            
            email.send_keys(os.getenv('LINKEDIN_EMAIL'))
            password.send_keys(os.getenv('LINKEDIN_PASSWORD'))
            
            self.driver.find_element(By.CSS_SELECTOR, '[type="submit"]').click()
            print("Login form submitted...")
            time.sleep(5)
            return True
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    def extract_post_content(self, post, max_retries=3):
        content_selectors = [
            '.feed-shared-update-v2__description-wrapper',
            '.feed-shared-text',
            '.feed-shared-update-v2__content',
            '.update-components-text',
            '.feed-shared-inline-show-more-text',
            '.feed-shared-text-view',
            'span.break-words',
            '.feed-shared-article__description',
            '.feed-shared-article__title'
        ]
        
        for attempt in range(max_retries):
            for selector in content_selectors:
                try:
                    elements = post.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        return ' '.join([elem.text for elem in elements if elem.text])
                except Exception:
                    continue
            time.sleep(1)
        return None

    def scroll_and_collect_posts(self, url, num_scrolls=5):
        posts = []
        try:
            print(f"Navigating to {url}...")
            self.driver.get(url)
            time.sleep(5)
            
            for scroll in range(num_scrolls):
                time.sleep(3)
                post_elements = self.driver.find_elements(By.CSS_SELECTOR, '.feed-shared-update-v2')
                
                for post in post_elements:
                    try:
                        content = self.extract_post_content(post)
                        if content:
                            timestamp = "Unknown"
                            reactions = "0"
                            
                            try:
                                time_elements = post.find_elements(By.CSS_SELECTOR, '.feed-shared-actor__sub-description')
                                if time_elements:
                                    timestamp = time_elements[0].text
                            except Exception:
                                pass
                            
                            try:
                                reaction_elements = post.find_elements(By.CSS_SELECTOR, '.social-details-social-counts__reactions-count')
                                if reaction_elements:
                                    reactions = reaction_elements[0].text
                            except Exception:
                                pass
                            
                            posts.append({
                                'content': content,
                                'timestamp': timestamp,
                                'reactions': reactions,
                                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                    except Exception as e:
                        print(f"Error processing post: {str(e)}")
                        continue
                
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            return pd.DataFrame(posts)
        except Exception as e:
            print(f"Error collecting posts: {str(e)}")
            return pd.DataFrame()

    def scrape_messages(self, num_scrolls=5):
        try:
            print("Navigating to messages...")
            self.driver.get('https://www.linkedin.com/messaging/')
            time.sleep(5)
            
            messages = []
            for scroll in range(num_scrolls):
                time.sleep(3)
                message_elements = self.driver.find_elements(By.CSS_SELECTOR, '.msg-s-message-list__event')
                
                for msg in message_elements:
                    try:
                        content = msg.find_element(By.CSS_SELECTOR, '.msg-s-event__content').text
                        timestamp = msg.find_element(By.CSS_SELECTOR, '.msg-s-message-group__timestamp').text
                        
                        messages.append({
                            'content': content,
                            'timestamp': timestamp,
                            'reactions': 'N/A',
                            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                    except Exception:
                        continue
                
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            return pd.DataFrame(messages)
        except Exception as e:
            print(f"Error collecting messages: {str(e)}")
            return pd.DataFrame()

    def close(self):
        if self.driver:
            self.driver.quit()

    def run_scraper(self, scrape_type='feed'):
        try:
            self.setup_driver()
            if self.login():
                print(f"Login successful, collecting {scrape_type}...")
                
                if scrape_type == 'feed':
                    df = self.scroll_and_collect_posts('https://www.linkedin.com/feed/')
                    output_file = 'linkedin_feed_posts.csv'
                elif scrape_type == 'user_posts':
                    df = self.scroll_and_collect_posts('https://www.linkedin.com/in/me/recent-activity/shares/')
                    output_file = 'linkedin_user_posts.csv'
                else:  # messages
                    df = self.scrape_messages()
                    output_file = 'linkedin_messages.csv'
                
                if not df.empty:
                    df.to_csv(output_file, index=False)
                    print(f"Data saved to {output_file}")
                    return df
                else:
                    print("No data collected")
                    return None
            else:
                print("Login failed")
                return None
        finally:
            self.close()