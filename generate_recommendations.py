import json
import os
from collections import Counter

def load_json_data(filename):
    """
    Load data from a JSON file.
    
    Args:
        filename: Name of the JSON file to load
    
    Returns:
        Data from the JSON file
    """
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found!")
        return None
    
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def get_user_anime_ids(user_animelist, status_filter='completed'):
    """
    Extract anime IDs from user's animelist.
    
    Args:
        user_animelist: User's anime list data
        status_filter: Filter by status (default: 'completed')
    
    Returns:
        Set of anime IDs the user has watched
    """
    anime_ids = set()
    anime_titles = {}
    
    for item in user_animelist:
        anime = item.get('node', {})
        list_status = item.get('list_status', {})
        
        # Filter by status if specified
        if status_filter and list_status.get('status') != status_filter:
            continue
        
        anime_id = anime.get('mal_id') or anime.get('id')
        title = anime.get('title')
        
        if anime_id:
            anime_ids.add(anime_id)
            anime_titles[anime_id] = title
    
    return anime_ids, anime_titles

def build_recommendation_map(recommendations_data):
    """
    Build a mapping of anime ID to its recommendations with vote counts.
    
    Args:
        recommendations_data: List of recommendation data
    
    Returns:
        Dictionary mapping anime_id -> list of recommended anime with votes
    """
    rec_map = {}
    
    for rec in recommendations_data:
        entry = rec.get('entry', [])
        votes = rec.get('votes', 1)  # Default to 1 if votes not present
        
        # Each recommendation has 2 anime that are recommended together
        if len(entry) >= 2:
            anime1 = entry[0]
            anime2 = entry[1]
            
            id1 = anime1.get('mal_id')
            id2 = anime2.get('mal_id')
            title1 = anime1.get('title')
            title2 = anime2.get('title')
            
            if id1 and id2:
                # If user watched anime1, recommend anime2
                if id1 not in rec_map:
                    rec_map[id1] = []
                rec_map[id1].append({'id': id2, 'title': title2, 'votes': votes})
                
                # If user watched anime2, recommend anime1
                if id2 not in rec_map:
                    rec_map[id2] = []
                rec_map[id2].append({'id': id1, 'title': title1, 'votes': votes})
    
    return rec_map

def generate_recommendations(user_anime_ids, user_anime_titles, rec_map):
    """
    Generate recommendations based on user's anime list.
    
    Args:
        user_anime_ids: Set of anime IDs the user has watched
        user_anime_titles: Dictionary of anime ID to title
        rec_map: Dictionary mapping anime_id -> list of recommended anime
    
    Returns:
        List of tuples (anime_id, title, count) sorted by frequency
    """
    recommendation_counter = Counter()
    recommendation_titles = {}
    
    print(f"\nAnalyzing recommendations for {len(user_anime_ids)} anime in user's list...")
    print("-" * 60)
    
    for anime_id in user_anime_ids:
        if anime_id in rec_map:
            recommendations = rec_map[anime_id]
            user_title = user_anime_titles.get(anime_id, 'Unknown')
            
            print(f"Found {len(recommendations)} recommendations for: {user_title}")
            
            for rec in recommendations:
                rec_id = rec['id']
                rec_title = rec['title']
                rec_votes = rec.get('votes', 1)  # Get votes count
                
                # Don't recommend anime the user has already watched
                if rec_id not in user_anime_ids:
                    recommendation_counter[rec_id] += rec_votes  # Add votes instead of just 1
                    recommendation_titles[rec_id] = rec_title
    
    # Sort by frequency (most recommended first)
    sorted_recommendations = [
        (anime_id, recommendation_titles[anime_id], count)
        for anime_id, count in recommendation_counter.most_common()
    ]
    
    return sorted_recommendations

def save_recommendations(recommendations, filename='user_recommendations.json'):
    """
    Save recommendations to a JSON file.
    
    Args:
        recommendations: List of (anime_id, title, count) tuples
        filename: Output filename
    """
    # Convert to list of dictionaries for JSON
    rec_list = [
        {
            'anime_id': anime_id,
            'title': title,
            'recommendation_count': count
        }
        for anime_id, title, count in recommendations
    ]
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(rec_list, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved {len(rec_list)} recommendations to {filename}")

def print_recommendations(recommendations, top_n=50):
    """
    Print the top N recommendations.
    
    Args:
        recommendations: List of (anime_id, title, count) tuples
        top_n: Number of top recommendations to display
    """
    print(f"\n{'='*70}")
    print(f"TOP {min(top_n, len(recommendations))} RECOMMENDED ANIME")
    print(f"{'='*70}\n")
    print(f"{'Rank':<6} {'Title':<50} {'Times Recommended':<20}")
    print("-" * 70)
    
    for i, (anime_id, title, count) in enumerate(recommendations[:top_n], 1):
        print(f"{i:<6} {title[:50]:<50} {count:<20}")

if __name__ == "__main__":
    # Configuration
    USERNAME = "idiotcomputer"  # Change to desired username
    USER_LIST_FILE = f"{USERNAME}_animelist.json"
    RECOMMENDATIONS_FILE = f"{USERNAME}_recommendations.json"
    OUTPUT_FILE = f"{USERNAME}_personalized_recommendations.json"
    STATUS_FILTER = "completed"  # Only consider completed anime
    TOP_N = 100  # Number of recommendations to display
    
    print("=== Anime Recommendation Generator ===\n")
    
    # Load user's anime list
    print(f"Loading user list: {USER_LIST_FILE}")
    user_data = load_json_data(USER_LIST_FILE)
    if not user_data:
        exit(1)
    
    # Load recommendations data
    print(f"Loading recommendations: {RECOMMENDATIONS_FILE}")
    recommendations_data = load_json_data(RECOMMENDATIONS_FILE)
    if not recommendations_data:
        exit(1)
    
    # Extract user's anime IDs
    user_anime_ids, user_anime_titles = get_user_anime_ids(user_data, STATUS_FILTER)
    print(f"\nFound {len(user_anime_ids)} {STATUS_FILTER} anime in user's list")
    
    # Build recommendation map
    print(f"\nBuilding recommendation map from {len(recommendations_data)} recommendation entries...")
    rec_map = build_recommendation_map(recommendations_data)
    print(f"Mapped recommendations for {len(rec_map)} unique anime")
    #print(rec_map.keys())
    # Generate personalized recommendations
    personalized_recs = generate_recommendations(user_anime_ids, user_anime_titles, rec_map)
    
    # Print results
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Total unique recommendations found: {len(personalized_recs)}")
    
    print_recommendations(personalized_recs, TOP_N)
    
    # Save to file
    save_recommendations(personalized_recs, OUTPUT_FILE)
