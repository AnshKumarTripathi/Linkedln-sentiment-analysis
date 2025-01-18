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
    
    def extract_post_content(self, post):
        """Try multiple selectors to extract post content"""
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
        
        for selector in content_selectors:
            try:
                elements = post.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found content with selector: {selector}")
                    return ' '.join([elem.text for elem in elements if elem.text])
            except Exception as e:
                continue
        return None

    def scroll_and_collect_posts(self, num_scrolls=5):
        posts = []
        try:
            print("Navigating to feed...")
            self.driver.get('https://www.linkedin.com/feed/')
            time.sleep(5)
            
            print("Current URL:", self.driver.current_url)
            
            for scroll in range(num_scrolls):
                print(f"\nScroll attempt {scroll + 1}/{num_scrolls}")
                
                time.sleep(3)
                
                post_elements = self.driver.find_elements(By.CSS_SELECTOR, '.feed-shared-update-v2')
                print(f"Found {len(post_elements)} posts")
                
                for i, post in enumerate(post_elements):
                    try:
                        content = self.extract_post_content(post)
                        
                        if content:
                            print(f"\nPost {i+1} content preview: {content[:100]}...")
                            
                            timestamp = "Unknown"
                            try:
                                time_elements = post.find_elements(By.CSS_SELECTOR, '.feed-shared-actor__sub-description')
                                if time_elements:
                                    timestamp = time_elements[0].text
                            except Exception as e:
                                print(f"Timestamp error: {str(e)}")
                            
                            reactions = "0"
                            try:
                                reaction_elements = post.find_elements(By.CSS_SELECTOR, '.social-details-social-counts__reactions-count')
                                if reaction_elements:
                                    reactions = reaction_elements[0].text
                            except Exception as e:
                                print(f"Reactions error: {str(e)}")
                            
                            posts.append({
                                'content': content,
                                'timestamp': timestamp,
                                'reactions': reactions,
                                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            print(f"Successfully collected post {i+1}")
                        else:
                            print(f"No content found for post {i+1}")
                    
                    except Exception as e:
                        print(f"Error processing post {i+1}: {str(e)}")
                        continue
                
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                print("Scrolled down")
                time.sleep(3)
            
            return pd.DataFrame(posts)
            
        except Exception as e:
            print(f"Error collecting posts: {str(e)}")
            return pd.DataFrame()
    
    def close(self):
        if self.driver:
            self.driver.quit()

    def run_scraper(self):
        try:
            self.setup_driver()
            if self.login():
                print("Login successful, collecting posts...")
                df = self.scroll_and_collect_posts()
                if not df.empty:
                    output_file = os.path.join(os.path.expanduser("~"), 'Documents', 'linkedin_posts.csv')
                    df.to_csv(output_file, index=False)
                    print(f"\nData saved to {output_file}")
                    print(f"Total posts collected: {len(df)}")
                    print("\nFirst few posts:")
                    print(df[['content']].head())
                else:
                    print("No posts were collected")
            else:
                print("Login failed")
        finally:
            self.close()

if __name__ == "__main__":
    scraper = LinkedInScraper()
    scraper.run_scraper()