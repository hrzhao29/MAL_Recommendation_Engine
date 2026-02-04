import requests
import time
import json
import os
import math
import random
from jikanpy import Jikan

# MAL API Configuration
CLIENT_ID = ""  # REPLACE THIS WHEN COMMITTING!!!!

# Use Jikan for userupdates only
jikan = Jikan()

def load_user_animelist(filename):
    """Load user's anime list from JSON file."""
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found!")
        return []
    
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def extract_user_ratings(animelist):
    """
    Extract anime ratings and titles from user's list.
    
    Returns:
        tuple: (ratings_dict {anime_id: score}, titles_dict {anime_id: title})
    """
    ratings = {}
    titles = {}
    
    for item in animelist:
        anime = item.get('node', {})
        list_status = item.get('list_status', {})
        
        anime_id = anime.get('mal_id') or anime.get('id')
        score = list_status.get('score', 0)
        title = anime.get('title', f'Unknown (ID: {anime_id})')
        
        # Only include rated anime
        if anime_id and score > 0:
            ratings[anime_id] = score
            titles[anime_id] = title
    
    return ratings, titles

def get_users_from_anime(anime_id, max_users=50):
    """
    Get users who recently updated/rated a specific anime.
    
    Returns:
        list: List of usernames
    """
    try:
        print(f"  Fetching users for anime ID {anime_id}...")
        time.sleep(1)
        
        response = jikan.anime(anime_id, extension='userupdates')
        updates = response.get('data', [])
        
        usernames = []
        for update in updates[:max_users]:
            username = update.get('user', {}).get('username')
            if username:
                usernames.append(username)
        
        return usernames
        
    except Exception as e:
        print(f"  Error fetching users for anime {anime_id}: {e}")
        return []

def fetch_user_animelist(username, status_filter='completed'):
    """
    Fetch a user's anime list with ratings and titles using MAL API.
    
    Returns:
        list of dicts with {anime_id, title, score} or None if failed
    """
    try:
        print(f"    Fetching animelist for user: {username}...")
        time.sleep(1)
        
        all_anime = []
        offset = 0
        limit = 1000  # MAL API max limit
        
        headers = {'X-MAL-CLIENT-ID': CLIENT_ID}
        
        # Fetch all pages (usually just 1 with limit=1000)
        while True:
            url = f"https://api.myanimelist.net/v2/users/{username}/animelist"
            params = {
                'limit': limit,
                'offset': offset,
                'fields': 'list_status'
            }
            
            # Add status filter if not 'all'
            if status_filter != 'all':
                params['status'] = status_filter
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 404:
                print(f"    User not found or list is private")
                return None
            
            response.raise_for_status()
            
            data = response.json()
            anime_list = data.get('data', [])
            
            if not anime_list:
                break
            
            # Extract data
            for item in anime_list:
                anime = item.get('node', {})
                list_status = item.get('list_status', {})
                
                anime_id = anime.get('id')
                score = list_status.get('score', 0)
                title = anime.get('title', f'Unknown (ID: {anime_id})')
                
                # Only include rated anime
                if anime_id and score > 0:
                    all_anime.append({
                        'anime_id': anime_id,
                        'title': title,
                        'score': score
                    })
            
            # Check if there are more pages
            if 'next' not in data.get('paging', {}):
                break
            
            offset += limit
            time.sleep(1)
        
        return all_anime if all_anime else None
        
    except Exception as e:
        print(f"    Error fetching animelist for {username}: {e}")
        return None

def calculate_pearson_correlation(ratings1, ratings2):
    """
    Calculate Pearson correlation coefficient between two users.
    
    Args:
        ratings1, ratings2: dict of {anime_id: score}
    
    Returns:
        tuple: (correlation, num_shared_anime)
    """
    # Find shared anime
    shared_anime = set(ratings1.keys()) & set(ratings2.keys())
    
    if len(shared_anime) < 3:  # Need at least 3 shared anime
        return 0.0, 0
    
    # Get ratings for shared anime
    scores1 = [ratings1[anime_id] for anime_id in shared_anime]
    scores2 = [ratings2[anime_id] for anime_id in shared_anime]
    
    # Calculate means
    mean1 = sum(scores1) / len(scores1)
    mean2 = sum(scores2) / len(scores2)
    
    # Calculate Pearson correlation
    numerator = sum((s1 - mean1) * (s2 - mean2) for s1, s2 in zip(scores1, scores2))
    
    sum_sq1 = sum((s1 - mean1) ** 2 for s1 in scores1)
    sum_sq2 = sum((s2 - mean2) ** 2 for s2 in scores2)
    
    denominator = math.sqrt(sum_sq1 * sum_sq2)
    
    if denominator == 0:
        return 0.0, len(shared_anime)
    
    correlation = numerator / denominator
    
    # Apply significance weighting (penalize correlations with few shared items)
    significance = min(len(shared_anime) / 50.0, 1.0)
    weighted_correlation = correlation * significance
    
    return weighted_correlation, len(shared_anime)

def find_similar_users(target_ratings, target_animelist, num_anime_to_sample=20, users_per_anime=30, min_shared=10):
    """
    Find users similar to the target user.
    
    Returns:
        list: Similar users with their animelists
    """
    print("\nFinding similar users...")
    print(f"Sampling from {num_anime_to_sample} anime in target user's list")
    print("-" * 60)
    
    # Get anime IDs from target user (randomly sample from their rated anime)
    all_anime_ids = list(target_ratings.keys())
    random.shuffle(all_anime_ids)
    target_anime_ids = all_anime_ids[:num_anime_to_sample]
    
    # Collect candidate users
    candidate_users = set()
    
    for anime_id in target_anime_ids:
        usernames = get_users_from_anime(anime_id, users_per_anime)
        candidate_users.update(usernames)
        print(f"  Found {len(usernames)} users for anime {anime_id} (Total candidates: {len(candidate_users)})")
    
    print(f"\nTotal candidate users: {len(candidate_users)}")
    print("\nFetching animelists for candidate users...")
    
    # Randomly shuffle candidate users to get diverse sample
    candidate_users_list = list(candidate_users)
    random.shuffle(candidate_users_list)
    
    # Fetch animelists and calculate similarities
    similar_users = []
    
    for i, username in enumerate(candidate_users_list, 1):
        if i > 300:  # Limit to 300 users to avoid too many API calls
            print(f"\nReached limit of 300 users, stopping...")
            break
        
        print(f"[{i}/{min(len(candidate_users), 300)}] Processing user: {username}")
        
        user_animelist = fetch_user_animelist(username)
        
        if not user_animelist:
            continue
        
        # Convert to ratings dict for correlation calculation
        user_ratings = {item['anime_id']: item['score'] for item in user_animelist}
        
        # Calculate similarity
        correlation, num_shared = calculate_pearson_correlation(target_ratings, user_ratings)
        
        if num_shared >= min_shared and abs(correlation) > 0.1:
            similar_users.append({
                'username': username,
                'correlation': correlation,
                'num_shared': num_shared,
                'animelist': user_animelist  # Store full animelist with titles
            })
            print(f"    Similarity: {correlation:.3f}, Shared anime: {num_shared}, Total anime: {len(user_animelist)}")
    
    # Sort by correlation (descending)
    similar_users.sort(key=lambda x: x['correlation'], reverse=True)
    
    return similar_users

def save_similar_users(similar_users, target_username, output_dir='.'):
    """Save similar users data to files."""
    
    # Save summary (without full animelists)
    summary = [
        {
            'username': user['username'],
            'correlation': user['correlation'],
            'num_shared': user['num_shared'],
            'num_anime': len(user['animelist'])
        }
        for user in similar_users
    ]
    
    summary_file = os.path.join(output_dir, f'{target_username}_similar_users.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(similar_users)} similar users summary to {summary_file}")
    
    # Save detailed data (with full animelists including titles)
    detailed_file = os.path.join(output_dir, f'{target_username}_similar_users_detailed.json')
    with open(detailed_file, 'w', encoding='utf-8') as f:
        json.dump(similar_users, f, ensure_ascii=False, indent=2)
    print(f"Saved detailed similar users data to {detailed_file}")

if __name__ == "__main__":
    # Configuration
    TARGET_USERNAME = "idiotcomputer"
    USER_LIST_FILE = f"{TARGET_USERNAME}_animelist.json"
    
    # Parameters
    NUM_ANIME_TO_SAMPLE = 20  # How many anime from target user's list to sample users from
    USERS_PER_ANIME = 30      # How many users to fetch per anime
    MIN_SHARED_ANIME = 10     # Minimum shared anime to consider similarity
    
    print("=" * 70)
    print("FIND SIMILAR USERS")
    print("=" * 70)
    
    # Load target user's animelist
    print(f"\nLoading target user's list: {USER_LIST_FILE}")
    target_animelist = load_user_animelist(USER_LIST_FILE)
    
    if not target_animelist:
        print("Failed to load target user's anime list. Exiting.")
        exit(1)
    
    # Extract ratings
    target_ratings, _ = extract_user_ratings(target_animelist)
    print(f"Target user has {len(target_ratings)} rated anime")
    
    if len(target_ratings) < 10:
        print("Target user has too few ratings. Need at least 10 rated anime.")
        exit(1)
    
    # Find similar users
    similar_users = find_similar_users(
        target_ratings,
        target_animelist,
        num_anime_to_sample=NUM_ANIME_TO_SAMPLE,
        users_per_anime=USERS_PER_ANIME,
        min_shared=MIN_SHARED_ANIME
    )
    
    print(f"\nFound {len(similar_users)} similar users")
    
    if not similar_users:
        print("No similar users found. Try adjusting parameters.")
        exit(1)
    
    # Display top similar users
    print("\n" + "=" * 70)
    print("TOP 10 MOST SIMILAR USERS")
    print("=" * 70)
    print(f"{'Username':<20} {'Correlation':<15} {'Shared Anime':<15} {'Total Anime':<15}")
    print("-" * 70)
    
    for user in similar_users[:10]:
        print(f"{user['username']:<20} {user['correlation']:>10.3f}     {user['num_shared']:>10}     {len(user['animelist']):>10}")
    
    # Save results
    save_similar_users(similar_users, TARGET_USERNAME)
    
    print("\n" + "=" * 70)
    print("DONE! Run collaborative_filtering.py to generate recommendations.")
    print("=" * 70)
