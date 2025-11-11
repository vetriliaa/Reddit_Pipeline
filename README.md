# Reddit Pipeline

**Goal**: Demonstrate data extraction/normalization, database design, AI tool integration and **familiarity with Lumonic tools** (Python, SQL, Pydantic)

**Project overview**: Fetches 25 posts of live data from user-specified subreddits, analyzes the sentiment of each post, stores the structured data in a SQLite database and generates an HTML report summarizing insights.

**New Libraries**:
Pydantic was the first new library to me, and was helpful for validating data and keeping the database clean. I had to get used to the syntax but it quickly became clear how to validate data types and set default values. [This](https://medium.com/@marcnealer/a-practical-guide-to-using-pydantic-8aafa7feebf6) article was super helpful for a high level overview before I looked into more specific documentation.

I found this great library, Textblob, which was a really simple way to implement AI sentiment analysis on the data. It read each title and generate a polarity score, which was then classified as "Positive", "Negative", or "Neutral". 

**How to Use**: 
You can run this program in your terminal (after installing all the required libraries). You must list at least one subreddit you'd like data to be pulled from. 
Optional:
1. You can add "--limit INT" to your command to set a different number of posts to be fetched. 2. You can also add "--output" to change the filename of the HTML report that's generated.
3. You can add "--db" to change the filename of the SQLite dabase file.

For example you might run: 
<img width="544" height="20" alt="Screenshot 2025-11-10 at 6 38 53 PM" src="https://github.com/user-attachments/assets/5ff8a6a9-7aac-49b3-b6ef-a40ad50aebf0" />

**Architecture**
1. Extract Data (RedditDataExtractor): Connects to Reddit API to pull raw data
2. Transform Data (normalize_post & TextBlob): Normalizes data into a structured format, uses TextBlog to calculate sentiment scores for each title
3. Load Data (DatabaseManager & SQLite): Stores validated data in SQLite database (data aggregation)
4. User Report (ReportGenerator): Generates HTML report with simple summary dashboard and ranking of top posts
