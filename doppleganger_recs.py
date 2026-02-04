import json
import os
from collections import defaultdict

def load_json_data(filename):
    """Load data from a JSON file."""
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found!")
        return None
    
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

def build_anime_titles_dict(target_titles, similar_users):
    """
    Build a comprehensive anime titles dictionary from all sources.
    
    Returns:
        dict: {anime_id: title}
    """
    all_titles = dict(target_titles)
    
    # Add titles from similar users' animelists
    for user in similar_users:
        for anime_item in user.get('animelist', []):
            anime_id = anime_item.get('anime_id')
            title = anime_item.get('title')
            if anime_id and title:
                all_titles[anime_id] = title
    
    return all_titles

def generate_predictions(target_ratings, similar_users, anime_titles, top_k=30, min_raters=3):
    """
    Generate predicted ratings for unwatched anime based on similar users.
    
    Returns:
        list: Predictions with anime_id, title, predicted_score, confidence, num_raters
    """
    print("\nGenerating predictions...")
    print("-" * 60)
    
    # Calculate target user's mean rating
    target_mean = sum(target_ratings.values()) / len(target_ratings)
    
    # Use top K similar users
    top_similar = similar_users[:top_k]
    print(f"Using top {len(top_similar)} similar users")
    
    # Collect candidate anime (anime that similar users rated but target hasn't)
    candidate_anime = defaultdict(list)
    
    for user_data in top_similar:
        correlation = user_data['correlation']
        animelist = user_data['animelist']
        
        # Convert animelist to ratings dict
        user_ratings = {item['anime_id']: item['score'] for item in animelist}
        user_mean = sum(user_ratings.values()) / len(user_ratings)
        
        for anime_id, score in user_ratings.items():
            if anime_id not in target_ratings:
                # Store (correlation, centered_rating)
                centered_rating = score - user_mean
                candidate_anime[anime_id].append((correlation, centered_rating))
    
    # Calculate predictions
    predictions = []
    
    for anime_id, rating_data in candidate_anime.items():
        if len(rating_data) < min_raters:
            continue
        
        # Weighted sum of centered ratings
        numerator = sum(corr * centered_rating for corr, centered_rating in rating_data)
        denominator = sum(abs(corr) for corr, _ in rating_data)
        
        if denominator == 0:
            continue
        
        predicted_score = target_mean + (numerator / denominator)
        
        # Clamp to valid range
        predicted_score = max(1, min(10, predicted_score))
        
        # Confidence based on number of raters and average correlation
        avg_correlation = sum(abs(corr) for corr, _ in rating_data) / len(rating_data)
        confidence = avg_correlation * min(len(rating_data) / 10.0, 1.0)
        
        predictions.append({
            'anime_id': anime_id,
            'title': anime_titles.get(anime_id, f'Unknown (ID: {anime_id})'),
            'predicted_score': predicted_score,
            'confidence': confidence,
            'num_raters': len(rating_data)
        })
    
    # Sort by predicted score (descending), then by confidence
    predictions.sort(key=lambda x: (x['predicted_score'], x['confidence']), reverse=True)
    
    return predictions

def save_recommendations(predictions, target_username, output_dir='.'):
    """Save recommendations to file."""
    recommendations_file = os.path.join(output_dir, f'{target_username}_dg_recommendations.json')
    with open(recommendations_file, 'w', encoding='utf-8') as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(predictions)} recommendations to {recommendations_file}")

def print_recommendations(predictions, top_n=20):
    """Print top recommendations."""
    print("\n" + "=" * 80)
    print(f"TOP {min(top_n, len(predictions))} PREDICTED RECOMMENDATIONS")
    print("=" * 80)
    print(f"{'Rank':<6} {'Title':<50} {'Predicted Score':<18} {'Confidence':<12}")
    print("-" * 80)
    
    for i, pred in enumerate(predictions[:top_n], 1):
        title = pred['title'][:48]
        score = pred['predicted_score']
        confidence = pred['confidence']
        print(f"{i:<6} {title:<50} {score:>13.2f}     {confidence:>10.3f}")

if __name__ == "__main__":
    # Configuration
    TARGET_USERNAME = "idiotcomputer"
    USER_LIST_FILE = f"{TARGET_USERNAME}_animelist.json"
    SIMILAR_USERS_FILE = f"{TARGET_USERNAME}_similar_users_detailed.json"
    
    # Parameters
    TOP_K_USERS = 30          # Number of similar users to use for predictions
    MIN_RATERS = 3            # Minimum similar users who rated an anime to make prediction
    
    print("=" * 80)
    print("COLLABORATIVE FILTERING RECOMMENDATION SYSTEM")
    print("=" * 80)
    
    # Load target user's animelist
    print(f"\nLoading target user's list: {USER_LIST_FILE}")
    target_animelist = load_json_data(USER_LIST_FILE)
    
    if not target_animelist:
        print("Failed to load target user's anime list. Exiting.")
        exit(1)
    
    # Extract ratings and titles
    target_ratings, target_titles = extract_user_ratings(target_animelist)
    print(f"Target user has {len(target_ratings)} rated anime")
    
    # Load similar users
    print(f"\nLoading similar users: {SIMILAR_USERS_FILE}")
    similar_users = load_json_data(SIMILAR_USERS_FILE)
    
    if not similar_users:
        print("Failed to load similar users. Run find_similar_users.py first.")
        exit(1)
    
    print(f"Loaded {len(similar_users)} similar users")
    
    # Build comprehensive anime titles dictionary
    anime_titles = build_anime_titles_dict(target_titles, similar_users)
    print(f"Collected titles for {len(anime_titles)} unique anime")
    
    # Generate predictions
    predictions = generate_predictions(
        target_ratings,
        similar_users,
        anime_titles,
        top_k=TOP_K_USERS,
        min_raters=MIN_RATERS
    )
    
    print(f"\nGenerated {len(predictions)} predictions")
    
    # Print results
    print_recommendations(predictions, top_n=20)
    
    # Save results
    save_recommendations(predictions, TARGET_USERNAME)
    
    print("\n" + "=" * 80)
    print("DONE!")
    print("=" * 80)
