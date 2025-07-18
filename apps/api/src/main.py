import logging
import collections
import re
from fastapi import FastAPI, HTTPException, Query
from typing import List, Dict, Annotated
from enum import Enum
from datetime import date, timedelta
from pydantic import BaseModel

from .services.github_service import GitHubService, REPO_OWNER, REPO_NAME
from fastapi.responses import JSONResponse
from .core.exceptions import GitHubServiceError

# --- Logging & App Setup ---
logger = logging.getLogger("uvicorn")
app = FastAPI(
    title="GitSight API",
    description="An API for analyzing the commit history of the OpenRA GitHub repository.",
    version="1.0.0",
)
@app.exception_handler(GitHubServiceError)
async def github_service_exception_handler(request, exc: GitHubServiceError):
    """Handles custom GitHub service errors and returns a clean JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": f"An error occurred: {exc.message}"},
    )
github_service = GitHubService(owner=REPO_OWNER, name=REPO_NAME)

# --- Models and Enums ---
class MetricType(str, Enum):
    commits = "commits"
    additions = "additions"
    deletions = "deletions"
    total_changes = "total_changes"

class CommitDeviation(BaseModel):
    sha: str
    title: str
    additions: int
    deletions: int
    total_changes: int
    z_score: float

# --- API Endpoints ---
@app.get("/health", tags=["Status"])
def health_check():
    """Check if the API is running."""
    logger.info("Health check endpoint was called.")
    return {"status": "ok"}

@app.get("/authors", response_model=List[str], tags=["Analysis"])
def get_unique_authors(
    start_date: Annotated[date, Query(description="Start date for the analysis (YYYY-MM-DD).")] = date.today() - timedelta(days=365),
    end_date: Annotated[date, Query(description="End date for the analysis (YYYY-MM-DD).")] = date.today() - timedelta(days=1)
):
    """
    Returns a sorted list of unique commit authors within the specified date range.
    Defaults to the last year.
    """
    logger.info(f"Endpoint /authors called with start: {start_date}, end: {end_date}")
    df = github_service.get_commit_data(str(start_date), str(end_date))
    
    if df.empty:
        return []
        
    return sorted(df['author_name'].unique().tolist())

@app.get("/commits/deviations", response_model=List[CommitDeviation], tags=["Analysis"])
def get_commit_deviations(
    start_date: Annotated[date, Query(description="Start date for the analysis.")] = date.today() - timedelta(days=365),
    end_date: Annotated[date, Query(description="End date for the analysis.")] = date.today() - timedelta(days=1)
):
    """
    Returns a list of commits with a significant deviation in size.
    
    A commit is considered a deviation if its total changes (additions + deletions)
    have a Z-score greater than 2, indicating it's significantly larger than the average.
    """
    logger.info(f"Endpoint /commits/deviations called with start: {start_date}, end: {end_date}")
    df = github_service.get_commit_data(str(start_date), str(end_date))
    
    if df.empty or len(df) < 2:
        return []
        
    df['total_changes'] = df['additions'] + df['deletions']
    mean = np.mean(df['total_changes'])
    std = np.std(df['total_changes'])
    
    if std == 0:
        return []

    df['z_score'] = df['total_changes'].apply(lambda x: (x - mean) / std)
    
    deviations = df[df['z_score'] > 2].copy()
    deviations.rename(columns={'oid': 'sha', 'messageHeadline': 'title'}, inplace=True)
    
    return deviations.to_dict(orient='records')

@app.get("/activity/weekly", response_model=Dict[str, int], tags=["Analysis"])
def get_weekly_activity(
    metric_type: Annotated[MetricType, Query(description="The metric to aggregate.")],
    author: Annotated[str, Query(description="Optional author name to filter by (case-insensitive).")] = None,
    start_date: Annotated[date, Query(description="Start date for the analysis.")] = date.today() - timedelta(days=365),
    end_date: Annotated[date, Query(description="End date for the analysis.")] = date.today() - timedelta(days=1)
):
    """
    Returns a sum of repository activity, aggregated by day of the week.
    
    This shows activity patterns (e.g., are people committing on weekends?).
    The results can be filtered by a specific author.
    """
    logger.info(f"Endpoint /activity/weekly called with metric: {metric_type}, start: {start_date}, end: {end_date}, author: {author}")
    df = github_service.get_commit_data(str(start_date), str(end_date))
    
    if df.empty:
        return {day: 0 for day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]}

    if author:
        df = df[df['author_name'].str.contains(author, case=False, na=False)]

    df['weekday'] = df['committedDate'].dt.day_name()
    
    if metric_type == MetricType.commits:
        activity = df.groupby('weekday').size()
    else:
        if metric_type == MetricType.total_changes:
            df['total_changes'] = df['additions'] + df['deletions']
        activity = df.groupby('weekday')[metric_type.value].sum()
        
    result = {day: 0 for day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]}
    result.update(activity.to_dict())
    
    return result

@app.get("/commits/word-frequency", response_model=Dict[str, int], tags=["Analysis"])
def get_word_frequency(
    start_date: Annotated[date, Query(description="Start date for the analysis.")] = date.today() - timedelta(days=365),
    end_date: Annotated[date, Query(description="End date for the analysis.")] = date.today() - timedelta(days=1)
):
    """
    Returns the frequency of the 100 most common words in commit messages,
    excluding common English stop words. This provides a high-level view of
    the project's focus during the time period.
    """
    logger.info(f"Endpoint /commits/word-frequency called with start: {start_date}, end: {end_date}")
    df = github_service.get_commit_data(str(start_date), str(end_date))

    if df.empty:
        return {}

    stop_words = set(['a', 'about', 'above', 'after', 'again', 'all', 'am', 'an', 'and', 'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'by', 'can', 'did', 'do', 'does', 'doing', 'down', 'during', 'each', 'for', 'from', 'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'just', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor', 'not', 'now', 'of', 'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'out', 'over', 'own', 's', 'same', 'she', 'should', 'so', 'some', 'such', 't', 'than', 'that', 'the', 'their', 'theirs', 'them', 'then', 'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with', 'you', 'your', 'yours', 'fix', 'update', 'add', 'remove', 'refactor', 'merge', 'pull', 'request', 'branch'])
    text = ' '.join(df['messageHeadline'].dropna())
    words = re.findall(r'\b\w+\b', text.lower())
    filtered_words = [word for word in words if word not in stop_words and not word.isdigit()]
    word_counts = collections.Counter(filtered_words)
    
    return dict(word_counts.most_common(100))