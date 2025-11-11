# This program pulls post from specificed subreddits, 
# conducts basic sentiment analysis, stores everything
# in a SQLite file and generates an HTML report

import requests
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from textblob import TextBlob

# Data validation and normalization via Pydantic
class RedditPost(BaseModel):
    post_id: str = Field(..., description="Unique Reddit post ID")
    subreddit: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    author: str = Field(default="[deleted]")
    score: int = Field(default=0, ge=0)
    num_comments: int = Field(default=0, ge=0)
    upvote_ratio: float = Field(default=0.5, ge=0.0, le=1.0)

    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    fetched_at: datetime = Field(default_factory=datetime.now)

# Extract data from Reddit
class RedditDataExtractor:
    def __init__(self):
        pass

    def fetch_subreddit(self, subreddit: str, limit: int = 25) -> List[dict]:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json"
        
        try:
            response = requests.get(url, headers = {"User-Agent": "Any string"})
            data = response.json()
            return data["data"]["children"]
        except Exception as e:
            print(f"Error fetching r/{subreddit}: {e}.")
    
    def normalize_post(self, raw_post: dict, subreddit: str) -> Optional[RedditPost]:
        """
        Normalize and validate raw Reddit post data.
        
        Args:
            raw_post: Raw post data from Reddit API
            subreddit: Subreddit name for context
            
        Returns:
            Validated RedditPost object or None if validation fails
        """
        try:
            post_data = raw_post["data"]
            title = post_data["title"]

            # Perform sentiment analysis on title via TextBlob
            blob = TextBlob(title)
            sentiment_score = blob.sentiment.polarity
            
            # Classify sentiment
            if sentiment_score > 0.1:
                sentiment_label = "Positive"
            elif sentiment_score < -0.1:
                sentiment_label = "Negative"
            else:
                sentiment_label = "Neutral"
            
            return RedditPost(
                post_id=post_data["id"],         
                subreddit=subreddit,
                title=title,
                author=post_data["author"],    
                score=post_data["score"],         
                num_comments=post_data["num_comments"], 
                upvote_ratio=post_data["upvote_ratio"], 
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label
            )
        except Exception as e:
            print(f"Error normalizing post: {e}")
            return None

class DatabaseManager:
    """Manages SQLite database operations (PostgreSQL-compatible syntax)."""
    
    def __init__(self, db_path: str = "reddit_analytics.db"):
        self.db_path = db_path
        self._create_tables()
    
    def _create_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                post_id TEXT PRIMARY KEY,
                subreddit TEXT NOT NULL,
                title TEXT NOT NULL,
                author TEXT,
                score INTEGER,
                num_comments INTEGER,
                upvote_ratio REAL,
                sentiment_score REAL,
                sentiment_label TEXT,
                fetched_at TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def insert_posts(self, posts: List[RedditPost]) -> int:
        """
        Insert posts into database (upsert on conflict).
        
        Returns:
            Number of posts inserted
        """
        conn = sqlite3.connect(self.db_path) 
        cursor = conn.cursor()
        inserted = 0

        for post in posts:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO posts 
                    (post_id, subreddit, title, author, score, num_comments, 
                     upvote_ratio, sentiment_score, 
                     sentiment_label, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post.post_id, post.subreddit, post.title, post.author,
                    post.score, post.num_comments, post.upvote_ratio,
                    post.sentiment_score, post.sentiment_label, 
                    post.fetched_at.isoformat()
                ))
                conn.commit()
                inserted += 1

            except Exception as e:
                print(f"Error inserting post {post.post_id}: {e}")
        
        conn.close()
        return inserted
    
    def get_analytics(self) -> dict:
        """
        Generate analytics from stored posts.
        
        Returns:
            Dictionary with aggregated statistics
        """
        conn = sqlite3.connect(self.db_path) 
        cursor = conn.cursor()
        
        # Overall stats
        cursor.execute("""
            SELECT 
                COUNT(*),
                AVG(score),
                AVG(num_comments)
            FROM posts
        """)

        raw_overall = cursor.fetchone()
        overall = {
            "total_posts": raw_overall[0],
            "avg_score": raw_overall[1],
            "avg_comments": raw_overall[2]
        }
        
        # Most positive post
        cursor.execute("""
            SELECT title FROM posts
            ORDER BY sentiment_score DESC
            LIMIT 1
        """)
        most_positive_row = cursor.fetchone()
        most_positive_title = most_positive_row[0]

        # Most negative post
        cursor.execute("""
            SELECT title FROM posts
            ORDER BY sentiment_score ASC
            LIMIT 1
        """)
        most_negative_row = cursor.fetchone()
        most_negative_title = most_negative_row[0]

        # Sentiment distribution
        cursor.execute("""
            SELECT sentiment_label, COUNT(*)
            FROM posts
            GROUP BY sentiment_label
        """)

        sentiment_dist = {}
        for row in cursor.fetchall():
            sentiment_dist[row[0]] = row[1]
        
        # Top posts
        cursor.execute("""
            SELECT title, subreddit, score, sentiment_label
            FROM posts
            ORDER BY score DESC
            LIMIT 10
        """)
        top_posts_tuples = cursor.fetchall()
        conn.close()
        
        return {
            "overall": overall,
            "sentiment_distribution": sentiment_dist,
            "top_posts": top_posts_tuples,
            "most_positive_title": most_positive_title,
            "most_negative_title": most_negative_title
        }

# HTML-styled report
class ReportGenerator:
    def generate_html_report(analytics):
        """Generate an HTML report with inline visualizations."""
        f = open("report.html", "w")
        
        f.write("<html><body>")
        f.write("<h1>Reddit Report</h1>")
        f.write("<p>Generated at: " + str(datetime.now()) + "</p>")
        f.write("<hr>")

        # Overall Stats
        f.write("<h2>Overall Stats</h2>")
        f.write("<p>Total Posts: " + str(analytics['overall']['total_posts']) + "</p>")
        f.write("<p>Avg Score: " + str(analytics['overall']['avg_score']) + "</p>")
        f.write("<p>Avg Comments: " + str(analytics['overall']['avg_comments']) + "</p>")
    
        f.write("<hr>")

        # Sentiment data
        f.write("<h2>Sentiment</h2>")
        f.write("<p><b>Most Positive:</b> " + analytics['most_positive_title'] + "</p>")
        f.write("<p><b>Most Negative:</b> " + analytics['most_negative_title'] + "</p>")
        
        f.write("<p><b>Distribution:</b></p>") 

        for label in analytics['sentiment_distribution']:
            count = analytics['sentiment_distribution'][label]
            f.write("<p>" + label + ": " + str(count) + "</p>")

        # "Top Posts" table 
        f.write("<hr>")
        f.write("<h2>Top Posts</h2>")
        f.write("<table border='1' cellpadding='5' style='border-collapse: collapse; width: 100%;'>")
        f.write("<tr>")
        f.write("<th>Title</th>")
        f.write("<th>Subreddit</th>")
        f.write("<th>Score</th>")
        f.write("<th>Sentiment</th>") 
        f.write("</tr>")

        for post in analytics['top_posts']:
            title = post[0]
            subreddit = post[1]
            score = post[2]
            sentiment = post[3]
            
            f.write("<tr>")
            f.write("<td>" + title + "</td>")
            f.write("<td>r/" + subreddit + "</td>")
            f.write("<td>" + str(score) + "</td>")
            f.write("<td>" + sentiment.title() + "</td>")
            f.write("</tr>")
        
        f.write("</table>")
        f.write("</body></html>")
        f.close()
    
        print("Report generated.") 

def main():
    parser = argparse.ArgumentParser(
        description="Reddit Analytics Pipeline - Extract, store, and analyze Reddit data"
    )
    parser.add_argument(
        'subreddits',
        nargs='+',
        help='Subreddit names to fetch (e.g., python technology machinelearning)'
    )
    parser.add_argument(
        '-l', '--limit',
        type=int,
        default=25,
        help='Number of posts to fetch per subreddit (default: 25, max: 100)'
    )
    parser.add_argument(
        '-o', '--output',
        default='report.html',
        help='Output path for HTML report (default: report.html)'
    )
    parser.add_argument(
        '--db',
        default='reddit_analytics.db',
        help='Database path (default: reddit_analytics.db)'
    )
    
    args = parser.parse_args()
    
    print("Reddit Analytics Pipeline")
    print("=" * 50)
    
    # Extract data
    extractor = RedditDataExtractor()
    all_posts = []
    
    for subreddit in args.subreddits:
        print(f"\nFetching r/{subreddit}...")
        raw_posts = extractor.fetch_subreddit(subreddit, args.limit)
        
        for raw_post in raw_posts:
            post = extractor.normalize_post(raw_post, subreddit)
            if post:
                all_posts.append(post)
        
        print(f"Retrieved {len(raw_posts)} posts")
    
    print(f"\nStoring {len(all_posts)} posts in database")
    
    # Store in database
    db = DatabaseManager(args.db)
    inserted = db.insert_posts(all_posts)
    print(f"Inserted {inserted} posts")
    
    print(f"\nGenerating analytics")
    analytics = db.get_analytics()
    
    # Generate report
    print(f"\nCreating HTML report...")
    ReportGenerator.generate_html_report(analytics)
    
    print(f"\nPipeline complete!")
    print(f"   - Database: {args.db}")
    print(f"   - Report: {args.output}")

if __name__ == "__main__":
    main()