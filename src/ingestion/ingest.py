import requests
import gzip
import json

def ingest_hour(date: str, hour: int) -> list:
    url = f"https://data.gharchive.org/{date}-{hour}.json.gz"
    try: 
        response = requests.get(url, timeout=120)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Error fetching data for {date}-{hour}: {e}")

    records = []
    content = gzip.decompress(response.content)
    for line in content.splitlines():
        record = json.loads(line)
        records.append(record) 

    print(f" Hour {hour}: {len(records)} events")
    return records