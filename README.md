# Image Combination API

FastAPI service that downloads up to four images, labels each with text, and returns a composited PNG with quadrant layout and borders.

## Prerequisites

- Python 3.11+
- `pip`

## Installation

```bash
python3 -m pip install -r requirements.txt
```

## Running the API

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Example Request

```bash
curl -X POST \
  http://localhost:8000/combine \
  -H "Content-Type: application/json" \
  -o output.png \
  -d '{
        "items": [
          {
            "imageUrl": "https://raw.githubusercontent.com/github/explore/main/topics/python/python.png",
            "text": "Character 1"
          },
          {
            "imageUrl": "https://raw.githubusercontent.com/github/explore/main/topics/fastapi/fastapi.png",
            "text": "Character 2"
          }
        ]
      }'
```

`output.png` will contain the generated composite.

## Deploying to Render

1. Push this repository to your own Git provider (GitHub, GitLab, or Bitbucket).
2. In the Render dashboard, create a **Web Service** and connect it to the repository.
3. When prompted, set the following values:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variable**: `PYTHON_VERSION=3.11`
4. Click **Create Web Service**; Render will install dependencies, build the service, and expose a public URL once the deployment succeeds.
