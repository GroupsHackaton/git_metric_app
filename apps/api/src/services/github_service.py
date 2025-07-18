import os
import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import httpx
from dotenv import load_dotenv
from tqdm import tqdm

from ..core.exceptions import GitHubServiceError

# --- Logging Setup ---
logger = logging.getLogger("uvicorn")

# --- Load Environment Variables ---
load_dotenv()
GITHUB_API_URL = "https://api.github.com/graphql"
GITHUB_TOKEN = os.getenv("GITHUB_API_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")

# --- GraphQL Query ---
COMMIT_QUERY = """
query($owner: String!, $name: String!, $since: GitTimestamp!, $until: GitTimestamp!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, since: $since, until: $until, after: $cursor) {
            pageInfo { endCursor, hasNextPage }
            totalCount
            nodes {
              oid, author { name, user { login } }, messageHeadline, additions, deletions, committedDate
            }
          }
        }
      }
    }
  }
  rateLimit { cost, remaining, resetAt }
}
"""

class GitHubService:
    def __init__(self, owner: str, name: str):
        self.owner = owner
        self.name = name
        self.headers = {"Authorization": f"bearer {GITHUB_TOKEN}"}
        self.cache_dir = Path(__file__).parent.parent / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        logger.info(f"GitHubService initialized for repo: {owner}/{name}. Cache dir: {self.cache_dir}")

    def _get_state_path(self, cache_path: Path) -> Path:
        return cache_path.with_suffix('.state.json')

    def _save_state(self, state_path: Path, cursor: str, fetched_commits: list):
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state = {"last_cursor": cursor, "commits": fetched_commits}
        with open(state_path, 'w') as f:
            json.dump(state, f)

    def _load_state(self, state_path: Path) -> dict:
        if state_path.exists():
            with open(state_path, 'r') as f:
                return json.load(f)
        return None

    async def _fetch_page(self, client: httpx.AsyncClient, since: str, until: str, cursor: str = None) -> dict:
        variables = {"owner": self.owner, "name": self.name, "since": since, "until": until, "cursor": cursor}
        try:
            response = await client.post(GITHUB_API_URL, json={"query": COMMIT_QUERY, "variables": variables}, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            if "errors" in data:
                raise GitHubServiceError(message=f"GraphQL error: {data['errors'][0]['message']}", status_code=400)
            return data
        except httpx.HTTPStatusError as e:
            raise GitHubServiceError(message=f"GitHub API returned an error: {e.response.status_code}", status_code=e.response.status_code)
        except httpx.RequestError as e:
            raise GitHubServiceError(message="A network error occurred while contacting GitHub.", status_code=503)

    async def _get_or_fetch_data(self, start_date_str: str, end_date_str: str) -> pd.DataFrame:
        cache_file_name = f"{self.owner}_{self.name}_{start_date_str}_{end_date_str}.parquet"
        cache_path = self.cache_dir / cache_file_name
        state_path = self._get_state_path(cache_path)

        # --- NEW: Smart Cache Invalidation Logic ---
        if cache_path.exists():
            try:
                end_date_obj = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                yesterday = datetime.now().date() - timedelta(days=1)

                if end_date_obj < yesterday:
                    logger.info(f"Cache hit for historical data. Serving from {cache_path}")
                    return pd.read_parquet(cache_path)

                file_mod_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
                ttl = timedelta(hours=1)
                if (datetime.now() - file_mod_time) < ttl:
                    logger.info(f"Cache hit for recent data (within 1-hour TTL). Serving from {cache_path}")
                    return pd.read_parquet(cache_path)
                else:
                    logger.warning(f"Cache stale for recent data (older than 1 hour). Re-fetching.")
                    os.remove(cache_path)
            except Exception as e:
                logger.error(f"Error during cache validation, proceeding to fetch. Error: {e}")

        all_commits, cursor, state = [], None, self._load_state(state_path)
        if state:
            cursor, all_commits = state.get("last_cursor"), state.get("commits", [])
            logger.warning(f"Found state file, attempting to resume fetch from cursor: {cursor}")

        since_iso, until_iso = f"{start_date_str}T00:00:00Z", f"{end_date_str}T23:59:59Z"
        has_next_page, total_commits = True, -1
        
        async with httpx.AsyncClient() as client:
            if not state:
                logger.info("Performing initial fetch...")
                page_data = await self._fetch_page(client, since=since_iso, until=until_iso)
                history = page_data["data"]["repository"]["defaultBranchRef"]["target"]["history"]
                total_commits, all_commits = history["totalCount"], history["nodes"]
                has_next_page, cursor = history["pageInfo"]["hasNextPage"], history["pageInfo"]["endCursor"]
                if has_next_page: self._save_state(state_path, cursor, all_commits)
            
            with tqdm(total=total_commits, initial=len(all_commits), desc="Fetching Commits") as pbar:
                if total_commits == -1: pbar.set_postfix_str("Resuming...")

                while has_next_page:
                    page_data = await self._fetch_page(client, since=since_iso, until=until_iso, cursor=cursor)
                    history = page_data["data"]["repository"]["defaultBranchRef"]["target"]["history"]
                    if total_commits == -1: pbar.total, total_commits = history["totalCount"], history["totalCount"]
                    
                    new_commits = history["nodes"]
                    all_commits.extend(new_commits)
                    has_next_page, cursor = history["pageInfo"]["hasNextPage"], history["pageInfo"]["endCursor"]
                    pbar.update(len(new_commits))
                    if has_next_page: self._save_state(state_path, cursor, all_commits)

        if not all_commits:
            return pd.DataFrame()
            
        df = pd.DataFrame(all_commits)
        df['author_name'] = df['author'].apply(lambda x: x['name'] if x else 'Unknown')
        df.drop(columns=['author'], inplace=True)
        df['committedDate'] = pd.to_datetime(df['committedDate'])

        logger.info(f"Successfully fetched {len(df)} commits. Saving to cache: {cache_path}")
        df.to_parquet(cache_path, index=False)
        
        if state_path.exists():
            os.remove(state_path); logger.info(f"Removed state file: {state_path}")
        
        return df

    def get_commit_data(self, start_date_str: str, end_date_str: str) -> pd.DataFrame:
        logger.info(f"get_commit_data called for {start_date_str} to {end_date_str}")
        return asyncio.run(self._get_or_fetch_data(start_date_str, end_date_str))