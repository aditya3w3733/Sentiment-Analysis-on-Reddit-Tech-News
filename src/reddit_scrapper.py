import praw
import boto3
import mysql.connector
import pandas as pd
import re

# Your Reddit API credentials
reddit = praw.Reddit(
    client_id="your-credentials",
    client_secret="your-credentials",
    user_agent="your-credentials"
)

# Your RDS database credentials (replace with your actual values)
conn = mysql.connector.connect(
    database="reddit_summary",  #replace with your db name
    user="aditya3w3733",
    password="aditya3w3733",
    host="RDS-INSTANCE-ENDPOINT",
    port="3306"
)

def get_news_link(post_id):
    try:
        submission = reddit.submission(id=post_id)

        #Checks if the submission URL itself is the news link
        if not submission.is_self:  # Check if it's not a self-post (text post)
            return submission.url

        # If it's a self-post, search for potential links in the text
        link_pattern = r'https?://\S+'
        potential_links = re.findall(link_pattern, submission.selftext)
        if potential_links:
            return potential_links[0]

        return None  # No links found

    except Exception as e:
        print(f"Error retrieving news link for post {post_id}: {e}")
        return None
def fetch_and_store_data():
    subreddit = reddit.subreddit('technology')  

    posts_data = [] 
    comments_data = []  

    for submission in subreddit.top("week", limit=5):
        comments = [comment for comment in submission.comments.list() if isinstance(comment, praw.models.Comment)]

        news_link = get_news_link(submission.id)

        posts_data.append({
            "post_id": submission.id,
            "post_title": submission.title,
            "news_link": news_link,
            "post_creation_date": submission.created_utc,
        })

        for comment in comments:
            comments_data.append({
                "comment_id": comment.id,
                "post_id": submission.id,
                "comment": comment.body
            })

    posts_df = pd.DataFrame(posts_data)

    comments_df = pd.DataFrame(comments_data)

    write_to_mysql(posts_df, comments_df)

def write_to_mysql(posts_df, comments_df):
    try:
        cursor = conn.cursor()

        for _, row in posts_df.iterrows():
            cursor.execute("""
                INSERT INTO posts (post_id, post_title, news_link, post_creation_date)
                VALUES (%s, %s, %s, %s)
            """, (row['post_id'], row['post_title'], row['news_link'], row['post_creation_date']))

        for _, row in comments_df.iterrows():
            cursor.execute("""
                INSERT INTO comments (comment_id, post_id, comment)
                VALUES (%s, %s, %s)
            """, (row['comment_id'], row['post_id'], row['comment']))

        conn.commit()
        print("Data successfully written to MySQL database.")

    except Exception as e:
        print(f"Error writing data to MySQL database: {e}")
        conn.rollback()

    finally:
        cursor.close()

if __name__ == "__main__":
    fetch_and_store_data()
