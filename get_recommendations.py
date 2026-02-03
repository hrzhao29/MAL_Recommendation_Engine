from jikanpy import Jikan
import time
import json
import os

# Use public API with rate limiting
jikan = Jikan()

def load_user_animelist(filename):
    """
    Load user's anime list from JSON file.
    
    Args:
        filename: Path to the user's animelist JSON file
    
    Returns:
        List of anime data from user's list
    """
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found!")
        return []
    
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def get_anime_ids_from_user_list(user_animelist, status_filter='completed'):
    """
    Extract anime IDs and titles from user's animelist.
    
    Args:
        user_animelist: User's anime list data
        status_filter: Filter by status (default: 'completed', or 'all' for everything)
    
    Returns:
        Dictionary mapping anime_id -> title
    """
    anime_data = {}
    
    for item in user_animelist:
        anime = item.get('node', {})
        list_status = item.get('list_status', {})
        
        # Filter by status if specified
        if status_filter != 'all' and list_status.get('status') != status_filter:
            continue
        
        anime_id = anime.get('mal_id') or anime.get('id')
        title = anime.get('title')
        
        if anime_id and title:
            anime_data[anime_id] = title
    
    return anime_data

def get_recommendations_for_user_list(user_anime_data):
    """
    Fetch recommendations for all anime in user's list.
    
    Args:
        user_anime_data: Dictionary mapping anime_id -> title
    
    Returns:
        List of recommendation data dictionaries
    """
    all_recommendations = []
    total = len(user_anime_data)
    
    print(f"\nGetting recommendations for {total} anime from user's list...")
    
    for i, (anime_id, title) in enumerate(user_anime_data.items(), 1):
        try:
            print(f"[{i}/{total}] Fetching recommendations for: {title} (ID: {anime_id})...")
            time.sleep(1)  # Rate limiting
            
            response = jikan.anime(anime_id, extension='recommendations')
            recommendations = response.get('data', [])
            
            # Format as recommendation pairs with votes
            for rec in recommendations:
                entry = rec.get('entry', {})
                votes = rec.get('votes', 1)  # Default to 1 if votes not present
                if entry:
                    filtered_rec = {
                        'entry': [
                            {
                                'mal_id': anime_id,
                                'title': title
                            },
                            {
                                'mal_id': entry.get('mal_id'),
                                'title': entry.get('title')
                            }
                        ],
                        'votes': votes
                    }
                    all_recommendations.append(filtered_rec)
            
            print(f"  Retrieved {len(recommendations)} recommendations")
            
        except Exception as e:
            print(f"  Error: {e}")
            continue
    
    return all_recommendations

def save_recommendations_data(recommendations_list, filename='anime_recommendations.json'):
    """
    Save recommendations data to a JSON file.
    
    Args:
        recommendations_list: List of recommendation data dictionaries
        filename: Name of the output file
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(recommendations_list, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved {len(recommendations_list)} recommendations to {filename}")

if __name__ == "__main__":
    #Configuration
    USERNAME = "idiotcomputer"  # Change to desired username
    USER_LIST_FILE = f"{USERNAME}_animelist.json"
    STATUS_FILTER = "completed"  # 'completed', 'watching', 'plan_to_watch', or 'all'
    OUTPUT_FILE = f"{USERNAME}_recommendations.json"
    
    print("=== Anime Recommendation Fetcher ===\n")
    
    # Load user's anime list
    print(f"Loading user list: {USER_LIST_FILE}")
    user_animelist = load_user_animelist(USER_LIST_FILE)
    
    if not user_animelist:
        print("Failed to load user's anime list. Exiting.")
        exit(1)
    
    # Extract anime IDs and titles
    user_anime_data = get_anime_ids_from_user_list(user_animelist, STATUS_FILTER)
    print(f"Found {len(user_anime_data)} anime with status: {STATUS_FILTER}")
    
    # Fetch recommendations for each anime
    recommendations_data = get_recommendations_for_user_list(user_anime_data)
    
    # Save to file
    save_recommendations_data(recommendations_data, OUTPUT_FILE)
    
    # Display summary
    print(f"\n{'='*60}")
    print(f"Successfully retrieved {len(recommendations_data)} recommendation pairs!")
    print(f"\nFirst 5 recommendations:")
    for i, rec in enumerate(recommendations_data[:5], 1):
        entry = rec.get('entry', [])
        if len(entry) >= 2:
            print(f"  {i}. {entry[0].get('title')} → {entry[1].get('title')}")