import httpx
import os
from dotenv import load_dotenv
import time
import json
from datetime import datetime

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print ("Github token not found!!!")

def required_part_of_issue(raw_issue : dict) -> dict:
    return {
        # Text for search
        "number": raw_issue.get("number"),
        "title": raw_issue.get("title"),
        "body": raw_issue.get("body"),
        
        # Time split
        "state": raw_issue.get("state"),
        "created_at": raw_issue.get("created_at"),
        "closed_at": raw_issue.get("closed_at"),
        
        # Finding duplicates
        "labels": [label.get("name") for label in raw_issue.get("labels", [])],
        
        # Showing results
        "html_url": raw_issue.get("html_url"),
        
        # Skipping PRs (True if it's a PR, False if it's a normal issue)
        "is_pull_request": "pull_request" in raw_issue,
        
        # Deciding whose comments to fetch
        "comments_count": raw_issue.get("comments", 0)
    }

def cache_present(filepath : str) -> set:
    cached_numbers = set()
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        if "number" in record:
                            cached_numbers.add(record["number"])
                    except json.JSONDecodeError:
                        continue
    return cached_numbers

def fetch_repo_issue(repo_owner: str, repo_name: str, start_date_str):
    #Check if these are present or not
    dir_path = os.path.join("data", "raw")
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, f"{repo_name}.jsonl")
    
    cached_issue_numbers = cache_present(file_path)
    print(f"Loaded {len(cached_issue_numbers)} issues from local cache.")

    number_list = []

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"

    headers = {
        "Accept" : "application/vnd.github+json",
        "User-Agent" : "my-github-app",
        "Authorization" : f"Bearer {GITHUB_TOKEN}"
    }

    iso_start_date = f"{start_date_str}T00:00:00Z"
    window_start = datetime.strptime(start_date_str, "%Y-%m-%d")

    params = {
        "state": "all",
        "sort": "created",
        "direction": "desc",
        "since": iso_start_date,
        "per_page": 100
    }

    current_page = 1

    #Pagination
    with open(file_path, "a", encoding="utf-8") as jsonl_file:
        while url:
            response = httpx.get(url, headers=headers, params=params if current_page == 1 else None, timeout=30.0)

            #Rate limited
            remaining = response.headers.get("x-ratelimit-remaining")
            reset_time = response.headers.get("x-ratelimit-reset")

            if response.status_code == 401:
                print("Bad/Unauthorized GitHub Token. Stopping script.")
                return

            if response.status_code in [403, 429, 500] or (remaining and int(remaining) == 0):
                if reset_time:
                    sleep_duration = max(int(reset_time) - int(time.time()), 0) + 2
                    time.sleep(sleep_duration)
                    continue
            
            if response.status_code != 200:
                print(f"Stopping execution. API returned unexpected status: {response.status_code}")
                print(response.json())
                return
                
            items = response.json()
            
            if not items:
                print("No more items returned by the API. Window complete.")
                break

            for element in items:
                if "pull_request" in element:
                    continue

                created_at_dt = datetime.strptime(element["created_at"], "%Y-%m-%dT%H:%M:%SZ")

                if created_at_dt < window_start:
                    continue

                issue_number = element["number"]
                if issue_number in cached_issue_numbers:
                    continue

                required_part = required_part_of_issue(element)
                jsonl_file.write(json.dumps(required_part, ensure_ascii=False) + "\n")
                cached_issue_numbers.add(issue_number)
                number_list.append(issue_number)

            # Flush the changes in disk immediately
            jsonl_file.flush()
            print(f"Processed page {current_page} for this window.")

            if "next" in response.links:
                url = response.links["next"]["url"]
                current_page += 1
            else:
                url = None
            
    print(len(number_list))
    print(len(set(number_list)))

if __name__ == "__main__":
    fetch_repo_issue(repo_owner="microsoft", repo_name="vscode", start_date_str="2024-01-01")