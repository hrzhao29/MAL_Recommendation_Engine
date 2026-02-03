import json
import os

def load_anime_data(filename):
    """
    Load anime data from a JSON file.
    
    Args:
        filename: Name of the JSON file to load
    
    Returns:
        List of anime data dictionaries
    """
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found!")
        return []
    
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def print_titles_and_scores(anime_list):
    """
    Print titles and scores of all anime in the list.
    
    Args:
        anime_list: List of anime data dictionaries
    """
    print(f"\n{'='*60}")
    print(f"Found {len(anime_list)} anime")
    print(f"{'='*60}\n")
    
    for anime in anime_list:
        rank = anime.get('rank', 'N/A')
        title = anime.get('title', 'Unknown Title')
        score = anime.get('score', 'N/A')
        
        print(f"#{rank:3} | {title:45} | Score: {score}")

def print_user_animelist(user_anime_list):
    """
    Print titles and scores from a user's anime list.
    
    Args:
        user_anime_list: List of user anime data from MAL API
    """
    print(f"\n{'='*60}")
    print(f"Found {len(user_anime_list)} anime in user's list")
    print(f"{'='*60}\n")
    
    for item in user_anime_list:
        # Extract anime info from MAL API format
        anime = item.get('node', {})
        list_status = item.get('list_status', {})
        
        title = anime.get('title', 'Unknown Title')
        user_score = list_status.get('score', 'N/A')
        mal_score = anime.get('mean', 'N/A')
        status = list_status.get('status', 'N/A')
        episodes_watched = list_status.get('num_episodes_watched', 0)
        total_episodes = anime.get('num_episodes', '?')
        
        print(f"{title:45} | User: {user_score}/10 | MAL: {mal_score} | Status: {status:12} | Progress: {episodes_watched}/{total_episodes}")

def print_recommendations(recommendations_list, num_to_show=50):
    """
    Print recommendations (just titles).
    
    Args:
        recommendations_list: List of recommendation data or personalized recommendations
        num_to_show: Number of recommendations to display
    """
    print(f"\n{'='*60}")
    print(f"Showing {min(num_to_show, len(recommendations_list))} recommendations")
    print(f"{'='*60}\n")
    
    # Check if this is personalized recommendations (with recommendation_count)
    # or raw recommendations (with entry)
    for i, item in enumerate(recommendations_list[:num_to_show], 1):
        if 'title' in item and 'recommendation_count' in item:
            # Personalized recommendations format
            title = item.get('title', 'Unknown')
            count = item.get('recommendation_count', 0)
            print(f"{i:3}. {title} (recommended {count} times)")
        elif 'entry' in item:
            # Raw recommendations format
            entry = item.get('entry', [])
            if len(entry) >= 2:
                title1 = entry[0].get('title', 'Unknown')
                title2 = entry[1].get('title', 'Unknown')
                print(f"{i:3}. {title1} ↔ {title2}")
        else:
            # Unknown format, just try to get title
            title = item.get('title', str(item))
            print(f"{i:3}. {title}")

if __name__ == "__main__":
    print("\n=== Anime Data Processor ===\n")
    print("Choose an option:")
    print("1. Process top anime list")
    print("2. Process user's anime list")
    print("3. Process recommendations")
    
    choice = input("\nEnter choice (1, 2, or 3): ").strip()
    
    if choice == '1':
        # Process top anime list
        filename = 'top_anime_1_to_1000.json'
        anime_data = load_anime_data(filename)
        
        if anime_data:
            print_titles_and_scores(anime_data)
    
    elif choice == '2':
        # Process user's anime list
        username = input("Enter username (or leave blank for 'idiotcomputer'): ").strip()
        if not username:
            username = 'idiotcomputer'
        
        filename = f'{username}_animelist.json'
        user_data = load_anime_data(filename)
        
        if user_data:
            print_user_animelist(user_data)
            
            # Show statistics
            print(f"\n{'='*60}")
            print("Statistics:")
            scored_anime = [item for item in user_data if item.get('list_status', {}).get('score', 0) > 0]
            if scored_anime:
                avg_score = sum(item.get('list_status', {}).get('score', 0) for item in scored_anime) / len(scored_anime)
                print(f"  Total anime: {len(user_data)}")
                print(f"  Scored anime: {len(scored_anime)}")
                print(f"  Average user score: {avg_score:.2f}/10")
    if choice == '3':
        # Process recommendations
        print("\nAvailable recommendation files:")
        print("1. Raw recommendations (username_recommendations.json)")
        print("2. Personalized recommendations (username_personalized_recommendations.json)")
        
        rec_choice = input("\nChoose type (1 or 2): ").strip()
        
        if rec_choice == '1':
            username = input("Enter username (or leave blank for 'idiotcomputer'): ").strip()
            if not username:
                username = 'idiotcomputer'
            filename = f'{username}_recommendations.json'    
        else:
            username = input("Enter username (or leave blank for 'idiotcomputer'): ").strip()
            if not username:
                username = 'idiotcomputer'
            filename = f'{username}_personalized_recommendations.json'
        
        num_to_show = input("How many recommendations to show? (default: 50): ").strip()
        num_to_show = int(num_to_show) if num_to_show.isdigit() else 50
        
        recommendations_data = load_anime_data(filename)
        
        if recommendations_data:
            print_recommendations(recommendations_data, num_to_show)
    
    else:
        print("Invalid choice!")