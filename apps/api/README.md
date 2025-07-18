# GitSight Backend API

This is the backend service for the GitSight project. It's a FastAPI application that fetches and analyzes commit history from a public GitHub repository.

## Prerequisites

  - Python 3.13
  - Docker & Docker Compose

## Setup

1.  **Clone the repository** and navigate into the API directory:

    ```bash
    cd api
    ```

2.  **Create and activate a Python virtual environment**:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Create environment file**: Create a `.env` file in this directory by copying the example.

    ```bash
    cp .env.example .env
    ```

    Then, edit the `.env` file and add your **GitHub Personal Access Token**.

    *You'll need to create a `.env.example` file with the following content:*

    ```ini
    # .env.example
    GITHUB_API_TOKEN="your_personal_access_token_here"
    REPO_OWNER="OpenRA"
    REPO_NAME="OpenRA"
    ```

## Running the Application

There are three ways to run the application.

### 1\. Local Development (Uvicorn)

This method runs the server directly on your local machine and is best for active development.

```bash
uvicorn src.main:app --reload
```

### 2\. Docker Standalone

This method builds and runs the backend in a container without Docker Compose.

```bash
# Build the image from within the 'api' directory
docker build -t gitsight-api .

# Run the container
docker run --rm -p 8000:8000 --env-file ./.env gitsight-api
```

### 3\. Docker Compose (from Project Root)

This method orchestrates all services and is the required method for the final project submission. Run this from the **root directory** of the monorepo.

```bash
docker-compose up --build
```

## Testing

Once the application is running, you can test it in two ways:

1.  **Interactive Docs (Swagger UI)**: Navigate to `http://localhost:8000/docs` in your browser to see and interact with all the available endpoints.
2.  **Postman**: Use the provided Postman collection to run a full suite of tests against the API.

## API Endpoints

| Method | Path                        | Description                                                        |
| :----- | :-------------------------- | :----------------------------------------------------------------- |
| `GET`    | `/health`                   | Checks if the API is running.                                      |
| `GET`    | `/authors`                  | Returns a list of unique commit authors for a given date range.    |
| `GET`    | `/commits/deviations`       | Returns commits with a statistically significant size deviation.   |
| `GET`    | `/activity/weekly`          | Returns a summary of repository activity aggregated by weekday.    |
| `GET`    | `/commits/word-frequency`   | Returns the frequency of common words in commit messages.          |