from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import List

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError
from pydantic import AnyHttpUrl, BaseModel, Field


app = FastAPI(title="Image Combination API")

TARGET_WIDTH = 2560
TARGET_HEIGHT = 1408
RESAMPLE_LANCZOS = getattr(Image, "Resampling", Image).LANCZOS


class ImageTextItem(BaseModel):
    imageUrl: AnyHttpUrl = Field(..., description="HTTP URL pointing to the image to download")
    text: str = Field(..., min_length=1, description="Text label rendered above the image")


class CombineRequest(BaseModel):
    items: List[ImageTextItem]


async def fetch_image(client: httpx.AsyncClient, url: str) -> Image.Image:
    try:
        response = await client.get(url)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=400, detail=f"Failed to download image: {url}") from exc

    try:
        image = Image.open(BytesIO(response.content))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image content at: {url}") from exc

    return image.convert("RGBA")


def get_font(size: int) -> ImageFont.ImageFont:
    base_dir = Path(__file__).resolve().parent
    font_candidates = [
        base_dir / "fonts" / "DejaVuSans-Bold.ttf",
        base_dir / "fonts" / "DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf",
        "DejaVuSans.ttf",
    ]

    for candidate in font_candidates:
        try:
            return ImageFont.truetype(str(candidate), size)
        except OSError:
            continue

    return ImageFont.load_default()


def render_text_image(text: str, font: ImageFont.ImageFont) -> tuple[Image.Image, int, int]:
    text = text.strip()
    if not text:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0)), 1, 1

    # Get text dimensions
    dummy_image = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_image)
    text_bbox = dummy_draw.textbbox((0, 0), text, font=font)

    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Create image and draw text directly at final size
    text_image = Image.new("RGBA", (text_width, text_height), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_image)
    text_draw.text((-text_bbox[0], -text_bbox[1]), text, fill="black", font=font)

    return text_image, text_width, text_height


@app.post("/combine", response_class=Response)
async def combine_images(payload: CombineRequest) -> Response:
    items = payload.items
    if not 1 <= len(items) <= 4:
        raise HTTPException(status_code=400, detail="Provide between 1 and 4 items.")

    padding = 24
    text_to_image_spacing = 8
    border_width = 2
    max_image_edge = 1024
    font = get_font(60)  # Large font for crisp text on big images
    blocks: List[dict] = []

    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, read=20.0)) as client:
        for item in items:
            image = await fetch_image(client, str(item.imageUrl))
            resized = ImageOps.contain(image, (max_image_edge, max_image_edge))

            text = item.text.strip()
            text_image, text_width, text_height = render_text_image(text, font)

            blocks.append(
                {
                    "image": resized,
                    "text_image": text_image,
                    "text_width": text_width,
                    "text_height": text_height,
                }
            )

    max_content_width = max(max(block["image"].width, block["text_width"]) for block in blocks)
    max_image_height = max(block["image"].height for block in blocks)
    max_text_height = max(block["text_height"] for block in blocks)

    cell_width = max_content_width + 2 * padding
    cell_height = max_image_height + max_text_height + text_to_image_spacing + 2 * padding

    num_items = len(blocks)
    if num_items == 1:
        cols, rows = 1, 1
    elif num_items == 2:
        cols, rows = 2, 1
    else:
        cols, rows = 2, 2

    canvas_width = cell_width * cols
    canvas_height = cell_height * rows

    canvas = Image.new("RGB", (canvas_width, canvas_height), color="white")
    draw = ImageDraw.Draw(canvas)

    for index, block in enumerate(blocks):
        row = index // 2
        col = index % 2

        x_offset = col * cell_width
        y_offset = row * cell_height

        block_width = max(block["image"].width, block["text_width"]) + 2 * padding
        block_height = block["text_height"] + text_to_image_spacing + block["image"].height + 2 * padding

        horizontal_shift = (cell_width - block_width) // 2
        vertical_shift = (cell_height - block_height) // 2

        block_left = x_offset + horizontal_shift
        block_top = y_offset + vertical_shift

        text_x = block_left + (block_width - block["text_width"]) // 2
        text_y = block_top + padding

        text_image = block["text_image"]
        canvas.paste(text_image, (int(text_x), int(text_y)), text_image.split()[3])

        image_x = block_left + (block_width - block["image"].width) // 2
        image_y = text_y + block["text_height"] + text_to_image_spacing

        canvas.paste(block["image"], (int(image_x), int(image_y)), mask=block["image"])

        for i in range(border_width):
            draw.rectangle(
                [
                    x_offset + i,
                    y_offset + i,
                    x_offset + cell_width - 1 - i,
                    y_offset + cell_height - 1 - i,
                ],
                outline="black",
            )

    if canvas.size != (TARGET_WIDTH, TARGET_HEIGHT):
        scale_factor = min(TARGET_WIDTH / canvas.width, TARGET_HEIGHT / canvas.height)
        scaled_width = max(1, min(TARGET_WIDTH, int(canvas.width * scale_factor)))
        scaled_height = max(1, min(TARGET_HEIGHT, int(canvas.height * scale_factor)))
        scaled_canvas = canvas.resize((scaled_width, scaled_height), resample=RESAMPLE_LANCZOS)
        final_canvas = Image.new("RGB", (TARGET_WIDTH, TARGET_HEIGHT), color="white")
        paste_x = (TARGET_WIDTH - scaled_width) // 2
        paste_y = (TARGET_HEIGHT - scaled_height) // 2
        final_canvas.paste(scaled_canvas, (paste_x, paste_y))
        canvas = final_canvas

    output = BytesIO()
    # PNG compression is lossless - compress_level 6 is good balance of speed/size
    canvas.save(output, format="PNG", optimize=True, compress_level=6)
    output.seek(0)

    return Response(content=output.getvalue(), media_type="image/png")
