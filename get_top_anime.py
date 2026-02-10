from jikanpy import Jikan
import time
import json

# Use public API with rate limiting
jikan = Jikan()

def get_top_anime_by_rating(start_rank, end_rank):
    """
    Fetch top anime ranked from start_rank to end_rank (inclusive) by rating.
    
    Args:
        start_rank: Starting rank (e.g., 1 for #1 anime)
        end_rank: Ending rank (e.g., 50 for #50 anime)
    
    Returns:
        List of anime data dictionaries
    """
    all_anime = []
    
    # Calculate which pages we need (25 anime per page)
    start_page = ((start_rank - 1) // 25) + 1
    end_page = ((end_rank - 1) // 25) + 1
    
    print(f"Fetching top anime ranked #{start_rank} to #{end_rank}...")
    print(f"This will require {end_page - start_page + 1} API requests...")
    
    for page in range(start_page, end_page + 1):
        try:
            print(f"Fetching page {page}...")
            time.sleep(1)  # Rate limit: 1 request per second
            
            response = jikan.top(type='anime', page=page)#, filter='bypopularity')
            anime_list = response.get('data', [])
            
            for anime in anime_list:
                rank = anime.get('rank')
                if rank and start_rank <= rank <= end_rank:
                    all_anime.append(anime)
            
            print(f"  Retrieved {len(anime_list)} anime from page {page}")
            
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            continue
    
    # Sort by rank to ensure correct order
    all_anime.sort(key=lambda x: x.get('rank', float('inf')))
    
    return all_anime

def save_anime_data(anime_list, filename='top_anime_data.json'):
    """
    Save anime data to a JSON file.
    
    Args:
        anime_list: List of anime data dictionaries
        filename: Name of the output file
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(anime_list, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved {len(anime_list)} anime to {filename}")

if __name__ == "__main__":
    # Configure the rank range here
    START_RANK = 1
    END_RANK = 5000
    
    # Fetch the anime data
    anime_data = get_top_anime_by_rating(START_RANK, END_RANK)
    
    # Save to file
    save_anime_data(anime_data, f'top_anime_{START_RANK}_to_{END_RANK}.json')
    
    # Display summary
    print(f"\nSuccessfully retrieved {len(anime_data)} anime!")
    print("\nTop 5 from your selection:")
    for anime in anime_data[:5]:
        print(f"  #{anime.get('rank')}: {anime.get('title')} (Score: {anime.get('score')})")