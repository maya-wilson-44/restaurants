import praw
import pandas as pd
import streamlit as st
import datetime
import re
from collections import Counter

# Set up Reddit API credentials
def initialize_reddit():
    reddit = praw.Reddit(
        client_id='BUCY1MsPqwHZZS60c88mfA',
        client_secret='s4_lBBEdwkuIS9B2iPqz5VheEWQ2gw',
        user_agent="RestaurantFinder/1.0 by mwilson17frog"
    )
    return reddit

# Function to search for New Orleans restaurant posts
def search_nola_restaurants(reddit, subreddits=["NewOrleans", "AskNOLA", "FoodNOLA"], 
                           limit=100, time_filter="year"):
    restaurant_data = []
    
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        
        # Search for restaurant-related posts
        search_terms = ["restaurant", "restaurants", "food", "eat", "dining", "cuisine"]
        
        for term in search_terms:
            search_query = f"New Orleans {term}"
            search_results = subreddit.search(search_query, limit=limit, time_filter=time_filter)
            
            for post in search_results:
                # Extract post data
                post_data = {
                    "title": post.title,
                    "subreddit": subreddit_name,
                    "score": post.score,
                    "comments": post.num_comments,
                    "created_utc": datetime.datetime.fromtimestamp(post.created_utc),
                    "url": f"https://www.reddit.com{post.permalink}",
                    "selftext": post.selftext,
                    "id": post.id
                }
                
                # Add to our dataset
                restaurant_data.append(post_data)
    
    # Convert to DataFrame and remove duplicates
    df = pd.DataFrame(restaurant_data)
    df = df.drop_duplicates(subset=["id"])
    
    return df

# Extract restaurant names from text
def extract_restaurant_names(df):
    # This is a simplified approach - a more robust solution would use NLP
    # Create a list of common restaurant names in New Orleans
    known_restaurants = [
        "Commander's Palace", "Galatoire's", "Antoine's", "Brennan's", 
        "Dooky Chase", "Jacques-Imo's", "Cochon", "Bayona", "August",
        "Compère Lapin", "Herbsaint", "Shaya", "Upperline", "Brigtsen's",
        "Willie Mae's", "Clancy's", "Arnaud's", "GW Fins", "Peche"
    ]
    
    # Dictionary to store mentions
    restaurant_mentions = Counter()
    
    # Look for restaurant names in titles and text
    for _, row in df.iterrows():
        text = f"{row['title']} {row['selftext']}"
        text = text.lower()
        
        for restaurant in known_restaurants:
            if restaurant.lower() in text:
                restaurant_mentions[restaurant] += 1
                
        # Look for patterns like "X Restaurant" or restaurants in quotes
        potential_names = re.findall(r'"([^"]*restaurant[^"]*)"', text, re.IGNORECASE)
        potential_names += re.findall(r'"([^"]*café[^"]*)"', text, re.IGNORECASE)
        potential_names += re.findall(r'"([^"]*cafe[^"]*)"', text, re.IGNORECASE)
        potential_names += re.findall(r'"([^"]*bistro[^"]*)"', text, re.IGNORECASE)
        potential_names += re.findall(r'"([^"]*grill[^"]*)"', text, re.IGNORECASE)
        
        for name in potential_names:
            if len(name) > 5:  # Avoid very short matches
                restaurant_mentions[name.strip()] += 1
    
    return restaurant_mentions

# Streamlit app
def create_nola_restaurant_app():
    st.title("New Orleans Restaurant Finder")
    st.write("Discover popular restaurants in New Orleans based on Reddit discussions")
    
    # Initialize Reddit API
    reddit = initialize_reddit()
    
    # Sidebar filters
    st.sidebar.header("Search Options")
    selected_subreddits = st.sidebar.multiselect(
        "Select subreddits to search",
        ["NewOrleans", "AskNOLA", "FoodNOLA", "Louisiana", "food"],
        default=["NewOrleans", "AskNOLA"]
    )
    
    time_options = {
        "Past day": "day",
        "Past week": "week", 
        "Past month": "month",
        "Past year": "year",
        "All time": "all"
    }
    selected_time = st.sidebar.selectbox(
        "Time period",
        list(time_options.keys()),
        index=2
    )
    
    post_limit = st.sidebar.slider("Maximum posts to search", 50, 500, 100)
    
    if st.sidebar.button("Search Reddit"):
        with st.spinner("Searching Reddit for New Orleans restaurant information..."):
            # Get data
            df = search_nola_restaurants(
                reddit, 
                subreddits=selected_subreddits,
                limit=post_limit,
                time_filter=time_options[selected_time]
            )
            
            # Display basic stats
            st.write(f"Found {len(df)} relevant posts")
            
            # Extract restaurant mentions
            restaurant_mentions = extract_restaurant_names(df)
            
            # Display top restaurants
            st.header("Most Mentioned Restaurants")
            top_restaurants = pd.DataFrame({
                "Restaurant": restaurant_mentions.keys(),
                "Mentions": restaurant_mentions.values()
            })
            top_restaurants = top_restaurants.sort_values("Mentions", ascending=False).head(20)
            
            st.bar_chart(top_restaurants.set_index("Restaurant"))
            
            # Display recent posts
            st.header("Recent Relevant Posts")
            recent_posts = df.sort_values("created_utc", ascending=False).head(10)
            
            for _, post in recent_posts.iterrows():
                st.subheader(post["title"])
                st.write(f"Posted in r/{post['subreddit']} on {post['created_utc'].strftime('%Y-%m-%d')}")
                st.write(f"Score: {post['score']} | Comments: {post['comments']}")
                if len(post["selftext"]) > 300:
                    st.write(f"{post['selftext'][:300]}...")
                else:
                    st.write(post["selftext"])
                st.write(f"[View on Reddit]({post['url']})")
                st.markdown("---")

if __name__ == "__main__":
    create_nola_restaurant_app()