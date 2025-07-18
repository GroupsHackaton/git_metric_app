# src/main.py
import logging
import collections
import re
from fastapi import FastAPI, HTTPException, Query
from typing import List, Dict
from enum import Enum
from datetime import date, timedelta
from pydantic import BaseModel
import pandas as pd
import numpy as np

from fastapi.middleware.cors import CORSMiddleware

# Import the service and config
from .services.github_service import GitHubService, REPO_OWNER, REPO_NAME

# --- Logging Setup ---
logger = logging.getLogger("uvicorn")

# --- App Setup ---
app = FastAPI(
    title="GitSight API",
    description="An API for analyzing Git repository history.",
    version="1.0.0",
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
@app.get("/health")
def health_check():
    logger.info("Health check endpoint was called.")
    return {"status": "ok"}

@app.get("/authors", response_model=List[str], tags=["Analysis"])
def get_unique_authors(
    start_date: date = Query(default=lambda: date.today() - timedelta(days=365)),
    end_date: date = Query(default=lambda: date.today() - timedelta(days=1))
):
    """Returns a list of unique commit authors within the date constraints."""
    logger.info(f"Endpoint /authors called with start: {start_date}, end: {end_date}")
    df = github_service.get_commit_data(str(start_date), str(end_date))
    
    if df.empty:
        return []
        
    return sorted(df['author_name'].unique().tolist())

@app.get("/commits/deviations", response_model=List[CommitDeviation], tags=["Analysis"])
def get_commit_deviations(
    start_date: date = Query(default=lambda: date.today() - timedelta(days=365)),
    end_date: date = Query(default=lambda: date.today() - timedelta(days=1))
):
    """Returns commits with a significant deviation based on z-score > 2."""
    logger.info(f"Endpoint /commits/deviations called with start: {start_date}, end: {end_date}")
    df = github_service.get_commit_data(str(start_date), str(end_date))
    
    if df.empty or len(df) < 2:
        return []
        
    df['total_changes'] = df['additions'] + df['deletions']
    mean = np.mean(df['total_changes'])
    std = np.std(df['total_changes'])
    
    # Avoid division by zero if all changes are the same
    if std == 0:
        return []

    df['z_score'] = df['total_changes'].apply(lambda x: (x - mean) / std)
    
    deviations = df[df['z_score'] > 2].copy()
    deviations.rename(columns={'oid': 'sha', 'messageHeadline': 'title'}, inplace=True)
    
    return deviations.to_dict(orient='records')

@app.get("/activity/weekly", response_model=Dict[str, int], tags=["Analysis"])
def get_weekly_activity(
    metric_type: MetricType,
    start_date: date = Query(default=lambda: date.today() - timedelta(days=365)),
    end_date: date = Query(default=lambda: date.today() - timedelta(days=1)),
    author: str = Query(default=None)
):
    """Returns a sum of activity aggregated by day of the week."""
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
        
    # Ensure all days of the week are present in the final dict
    result = {day: 0 for day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]}
    result.update(activity.to_dict())
    
    return result

@app.get("/commits/word-frequency", response_model=Dict[str, int], tags=["Analysis"])
def get_word_frequency(
    start_date: date = Query(default=lambda: date.today() - timedelta(days=365)),
    end_date: date = Query(default=lambda: date.today() - timedelta(days=1))
):
    """Returns the frequency of words in commit messages."""
    logger.info(f"Endpoint /commits/word-frequency called with start: {start_date}, end: {end_date}")
    df = github_service.get_commit_data(str(start_date), str(end_date))

    if df.empty:
        return {}

    # Define a simple list of stop words
    stop_words = set([
        'a', 'about', 'above', 'after', 'again', 'all', 'am', 'an', 'and', 'any', 'are', 'as', 'at', 'be', 'because', 
        'been', 'before', 'being', 'by', 'can', 'did', 'do', 'does', 'doing', 'down', 'during', 'each', 'for', 'from', 
        'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 
        'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'just', 'me', 'more', 'most', 'my', 'myself', 
        'no', 'nor', 'not', 'now', 'of', 'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'out', 'over', 'own', 
        's', 'same', 'she', 'should', 'so', 'some', 'such', 't', 'than', 'that', 'the', 'their', 'theirs', 'them', 
        'then', 'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 
        'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with', 'you', 
        'your', 'yours', 'fix', 'update', 'add', 'remove', 'refactor', 'merge', 'pull', 'request', 'branch'
    ])

    text = ' '.join(df['messageHeadline'].dropna())
    words = re.findall(r'\b\w+\b', text.lower())
    
    filtered_words = [word for word in words if word not in stop_words and not word.isdigit()]
    
    word_counts = collections.Counter(filtered_words)
    
    return dict(word_counts.most_common(100))