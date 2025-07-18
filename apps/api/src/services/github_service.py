# src/services/github_service.py
import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import httpx
from dotenv import load_dotenv
from tqdm import tqdm

# --- Logging Setup ---
logger = logging.getLogger("uvicorn")
# --- End Logging Setup ---

# Load environment variables from .env file
load_dotenv()

GITHUB_API_URL = "https://api.github.com/graphql"
GITHUB_TOKEN = os.getenv("GITHUB_API_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")

# The GraphQL query to fetch commit history
COMMIT_QUERY = """
query($owner: String!, $name: String!, $since: GitTimestamp!, $until: GitTimestamp!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, since: $since, until: $until, after: $cursor) {
            pageInfo {
              endCursor
              hasNextPage
            }
            totalCount
            nodes {
              oid
              author {
                name
                user {
                  login
                }
              }
              messageHeadline
              additions
              deletions
              committedDate
            }
          }
        }
      }
    }
  }
  rateLimit {
    cost
    remaining
    resetAt
  }
}
"""

class GitHubService:
    """A service to fetch and cache commit data from the GitHub GraphQL API."""

    def __init__(self, owner: str, name: str):
        self.owner = owner
        self.name = name
        self.headers = {"Authorization": f"bearer {GITHUB_TOKEN}"}
        self.cache_dir = Path(__file__).parent.parent / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        logger.info(f"GitHubService initialized for repo: {owner}/{name}. Cache dir: {self.cache_dir}")

    async def _fetch_page(self, client: httpx.AsyncClient, since: str, until: str, cursor: str = None) -> dict:
        """Fetches a single page of commits from the GitHub API."""
        variables = {"owner": self.owner, "name": self.name, "since": since, "until": until, "cursor": cursor}
        try:
            response = await client.post(GITHUB_API_URL, json={"query": COMMIT_QUERY, "variables": variables}, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"An error occurred while requesting {e.request.url!r}.")
            raise

    async def _get_or_fetch_data(self, start_date_str: str, end_date_str: str) -> pd.DataFrame:
        """Orchestrates fetching data from cache or from the API."""
        cache_file_name = f"{self.owner}_{self.name}_{start_date_str.split('T')[0]}_{end_date_str.split('T')[0]}.parquet"
        cache_path = self.cache_dir / cache_file_name
        
        if cache_path.exists():
            logger.info("Cache hit! Loading data from file.")
            return pd.read_parquet(cache_path)
        
        logger.warning(f"Cache miss for {cache_path}. Fetching from GitHub API.")
        
        since_iso = f"{start_date_str}T00:00:00Z"
        until_iso = f"{end_date_str}T23:59:59Z"
        logger.info(f"Formatted dates for API call: since={since_iso}, until={until_iso}")
        
        all_commits = []
        has_next_page = True
        cursor = None
        
        async with httpx.AsyncClient() as client:
            logger.info("Performing initial fetch to get total commit count...")
            initial_data = await self._fetch_page(client, since=since_iso, until=until_iso)
            
            if "errors" in initial_data:
                logger.error(f"GraphQL errors: {initial_data['errors']}")
                return pd.DataFrame()
            
            history = initial_data["data"]["repository"]["defaultBranchRef"]["target"]["history"]
            total_commits = history["totalCount"]
            logger.info(f"Total commits to fetch in date range: {total_commits}")

            all_commits.extend(history["nodes"])
            has_next_page = history["pageInfo"]["hasNextPage"]
            cursor = history["pageInfo"]["endCursor"]

            with tqdm(total=total_commits, desc="Fetching Commits", unit="commit") as pbar:
                pbar.update(len(history["nodes"]))
                
                while has_next_page:
                    # THE FIX IS ON THE NEXT LINE: page_.data -> page_data
                    page_data = await self._fetch_page(client, since=since_iso, until=until_iso, cursor=cursor)
                    if "errors" in page_data:
                        logger.error(f"GraphQL errors on subsequent page: {page_data['errors']}")
                        break

                    history = page_data["data"]["repository"]["defaultBranchRef"]["target"]["history"]
                    new_commits = history["nodes"]
                    all_commits.extend(new_commits)
                    
                    has_next_page = history["pageInfo"]["hasNextPage"]
                    cursor = history["pageInfo"]["endCursor"]
                    pbar.update(len(new_commits))

        if not all_commits:
            logger.warning("No commits found for the given date range.")
            return pd.DataFrame()
            
        df = pd.DataFrame(all_commits)
        
        df['author_name'] = df['author'].apply(lambda x: x['name'] if x else 'Unknown')
        df.drop(columns=['author'], inplace=True)
        df['committedDate'] = pd.to_datetime(df['committedDate'])

        logger.info(f"Successfully fetched {len(df)} commits. Saving to cache: {cache_path}")
        df.to_parquet(cache_path, index=False)
        
        return df

    def get_commit_data(self, start_date_str: str, end_date_str: str) -> pd.DataFrame:
        """Public method to get commit data, using cache if available."""
        logger.info(f"get_commit_data called for {start_date_str} to {end_date_str}")
        return asyncio.run(self._get_or_fetch_data(start_date_str, end_date_str))