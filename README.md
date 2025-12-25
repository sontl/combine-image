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

## API Endpoints

### POST /combine

Combines up to 4 images with text labels into a single composite PNG.

**Example Request:**

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

### POST /insert-text

Inserts text into a single image and returns the result as PNG.

**Request Body:**
- `imageUrl` (required): HTTP URL of the image
- `text` (required): Text to insert
- `x` (optional): X coordinate for text placement (default: 0)
- `y` (optional): Y coordinate for text placement (default: 0)
- `font_size` (optional): Font size in pixels, 1-500 (default: 40)
- `color` (optional): Text color as name or hex value (default: "black")
- `border_color` (optional): Border color as name or hex value (default: "white")
- `border_width` (optional): Border width in pixels, 0-20 (default: 2)

**Example Request:**

```bash
curl -X POST \
  http://localhost:8000/insert-text \
  -H "Content-Type: application/json" \
  -o output.png \
  -d '{
        "imageUrl": "https://raw.githubusercontent.com/github/explore/main/topics/python/python.png",
        "text": "Hello World",
        "x": 50,
        "y": 100,
        "font_size": 60,
        "color": "red",
        "border_color": "white",
        "border_width": 3
      }'
```

`output.png` will contain the image with the inserted text and border.

## Using the `insert_text_into_image` Function

The `insert_text_into_image()` function allows you to add text directly to an image programmatically.

**Function Signature:**

```python
insert_text_into_image(
    image: Image.Image,
    text: str,
    position: tuple[int, int] = (0, 0),
    font_size: int = 40,
    color: str = "black",
) -> Image.Image
```

**Parameters:**
- `image`: PIL Image object to draw text on
- `text`: Text string to insert
- `position`: (x, y) coordinates for text placement (default: top-left)
- `font_size`: Font size in pixels (default: 40)
- `color`: Text color as name or hex value (default: "black")

**Example Usage:**

```python
from PIL import Image
from main import insert_text_into_image

# Load an image
img = Image.open("photo.png")

# Insert text at position (50, 100)
result = insert_text_into_image(
    img,
    "Hello World",
    position=(50, 100),
    font_size=60,
    color="red"
)

# Save the result
result.save("output.png")
```

## Deploying to Render

1. Push this repository to your own Git provider (GitHub, GitLab, or Bitbucket).
2. In the Render dashboard, create a **Web Service** and connect it to the repository.
3. When prompted, set the following values:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variable**: `PYTHON_VERSION=3.11`
4. Click **Create Web Service**; Render will install dependencies, build the service, and expose a public URL once the deployment succeeds.
