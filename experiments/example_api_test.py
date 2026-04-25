"""Example experiment: Testing an external API.

This is a scratch file to explore API behavior before implementing properly.
Delete this file when creating your own project.
"""

import json
from urllib.request import urlopen

# Quick and dirty API test - no error handling, just exploring


def fetch_sample_data():
    """Fetch sample data from a public API."""
    url = "https://jsonplaceholder.typicode.com/posts/1"

    with urlopen(url) as response:  # nosec B310
        data = json.loads(response.read().decode())

    print("Response:")
    print(json.dumps(data, indent=2))
    return data


def main():
    print("Testing API...")
    result = fetch_sample_data()
    print(f"\nTitle: {result.get('title', 'N/A')}")


if __name__ == "__main__":
    main()
