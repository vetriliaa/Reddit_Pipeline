# PART 1: Simple JSON output
import requests
import json

base_url = "https://www.reddit.com/r/politics.json" 

try:
    response = requests.get(base_url, headers = {"User-Agent":"python"})
    response.raise_for_status()
    data = response.json()
except json.JSONDecodeError:
    print("Invalid JSON Response from server")
    exit(1)
# print(data)

# Extract posts from JSON (children array nested in data)
posts = data["data"]["children"]

# Slice the list to print first 10 posts 
top_ten = posts[:10]
# print(top_ten)

# PART 2: Normalized output of first 10 posts
def normalized_output(top_ten):
    # Set up numbered list
    sum_comments = 0
    avg_upvote_ratio = 0
    for i, post in enumerate(top_ten, 1):
        single_post = post["data"]

        title = single_post.get("title", "No Title")
        author = single_post.get("author", "Anonymous")
        num_comments = single_post.get("num_comments", "Number of Comments unavailable")
        upvote_ratio = single_post.get("upvote_ratio", 0.5)

        print(f"{i}. {title}")
        print(f"Author: {author} | Upvote Ratio: {upvote_ratio} | Comments: {num_comments}")
       
        sum_comments += single_post["num_comments"]
        avg_upvote_ratio += single_post["upvote_ratio"]
        print()

    print(f"Average Comment Count: {sum_comments / 10.0} | Average Upvote Ratio: {avg_upvote_ratio / 10.0}")

normalized_output(top_ten)

# PART 3: Export first ten to a JSON file
def export_as_json(top_ten):
    posts_to_save = []
    
    for post in top_ten:
        single_post = post["data"]
        posts_to_save.append({
            "title": single_post.get("title", "No Title"),
            "author": single_post.get("author", "Anonymous"),
            "num_comments ": single_post.get("num_comments", "Number of Comments unavailable"),
            "upvote_ratio": single_post.get("upvote_ratio", 0.5)
        })

    try:
        with open('top_ten.json', 'w') as f:
            json.dump(posts_to_save, f, indent=2)
        print("Exported the top 10 as a json file!")
    except IOError as e:
        print(f"Error saving file: {e}")

export_as_json(top_ten)
