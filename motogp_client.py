import requests
import time

class MotoGPClient:
    def __init__(self):
        self.base_url_v1 = "https://api.pulselive.motogp.com/motogp/v1"
        self.base_url_v2 = "https://api.pulselive.motogp.com/motogp/v2"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Origin': 'https://www.motogp.com',
            'Referer': 'https://www.motogp.com/'
        }
        self._cache = {}
        self.cache_duration = 3600  # 1 ora

    def _fetch(self, url):
        """Metodo privato per gestire le chiamate e la cache"""
        if url in self._cache:
            data, timestamp = self._cache[url]
            if time.time() - timestamp < self.cache_duration:
                print(f"⚡ Cache hit per: {url}")
                return data
        
        print(f"🌐 Chiamata API: {url}")
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        
        self._cache[url] = (data, time.time())
        return data

    def get_events(self, season_uuid):
        url = f"{self.base_url_v1}/results/events?seasonUuid={season_uuid}"
        return self._fetch(url)

    def get_world_standings(self, season_uuid, category_uuid):
        url = f"{self.base_url_v2}/results/world-standings?type=rider&season={season_uuid}&category={category_uuid}"
        return self._fetch(url)

    def get_sessions(self, event_uuid, category_uuid):
        url = f"{self.base_url_v1}/results/sessions?eventUuid={event_uuid}&categoryUuid={category_uuid}"
        return self._fetch(url)

    def get_classifications(self, session_uuid):
        url = f"{self.base_url_v2}/results/classifications?session={session_uuid}"
        return self._fetch(url)
    
    def get_rider(self, category_uuid):
        url = f"{self.base_url_v1}/teams?categoryUuid={category_uuid}&seasonYear=2026"
        return self._fetch(url)