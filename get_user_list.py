import requests
import time
import json

# Get your Client ID from: https://myanimelist.net/apiconfig
CLIENT_ID = ""  # REPLACE THIS

def get_user_animelist(username, status='completed'):
    """
    Fetch user's anime list using official MAL API.
    No OAuth needed for public lists - just Client ID.
    """
    all_anime = []
    offset = 0
    limit = 1000
    
    print(f"Fetching anime list for user: {username}")
    print(f"Status filter: {status}")
    
    headers = {'X-MAL-CLIENT-ID': CLIENT_ID}
    
    while True:
        try:
            print(f"Fetching offset {offset}...")
            time.sleep(1)
            
            url = f"https://api.myanimelist.net/v2/users/{username}/animelist"
            params = {
                'limit': limit,
                'offset': offset,
                'status': status,
                'fields': 'list_status,num_episodes,mean,genres,synopsis'
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            anime_list = data.get('data', [])
            
            if not anime_list:
                break
            
            all_anime.extend(anime_list)
            print(f"  Retrieved {len(anime_list)} anime (Total: {len(all_anime)})")
            
            if 'next' not in data.get('paging', {}):
                break
            
            offset += limit
            
        except Exception as e:
            print(f"Error: {e}")
            break
    
    return all_anime

def save_user_list(anime_list, username, filename=None):
    if filename is None:
        filename = f'{username}_animelist.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(anime_list, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved {len(anime_list)} anime to {filename}")

if __name__ == "__main__":
    USERNAME = "idiotcomputer"
    STATUS_FILTER = "completed"
    
    user_anime_data = get_user_animelist(USERNAME, STATUS_FILTER)
    save_user_list(user_anime_data, USERNAME)
    
    print(f"\nSuccessfully retrieved {len(user_anime_data)} anime!")