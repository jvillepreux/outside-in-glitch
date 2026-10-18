import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError


def outside_in_order(count):
    """Return indices 0..count-1 taken alternately from both ends: 0, n-1, 1, n-2, ..."""
    order = []
    low, high = 0, count - 1
    while low < high:
        order += [low, high]
        low += 1
        high -= 1
    if low == high:
        order.append(low)
    return order


def mirror_quadrants(pixels):
    wide = np.concatenate([pixels, pixels[:, ::-1]], axis=1)
    return np.concatenate([wide, wide[::-1]], axis=0)


def snap(length, count):
    """Nearest multiple of count to length, never below count."""
    return max(count, count * round(length / count))


def resize(pixels, width, height):
    if pixels.shape[:2] == (height, width):
        return pixels
    image = Image.fromarray(pixels).resize((width, height), Image.Resampling.LANCZOS)
    return np.asarray(image)


def interleave(pixels, count, axis):
    strips = np.split(pixels, count, axis=axis)
    return np.concatenate([strips[i] for i in outside_in_order(count)], axis=axis)


def glitch(image, strips=40, grayscale=False):
    image = ImageOps.exif_transpose(image)
    if grayscale:
        image = image.convert("L")
    pixels = mirror_quadrants(np.asarray(image.convert("RGB")))
    height, width = pixels.shape[:2]

    width = snap(width, strips)
    pixels = resize(pixels, width, height)
    pixels = interleave(pixels, strips, axis=1)

    size = width // strips
    rows = max(1, round(height / size))
    pixels = resize(pixels, width, rows * size)
    pixels = interleave(pixels, rows, axis=0)

    return Image.fromarray(pixels)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a mirrored strip-interleaving glitch from an image."
    )
    parser.add_argument("input", type=Path, help="source image (JPG, PNG, ...)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output path, format follows the extension (default: <input>_glitch, same extension)",
    )
    parser.add_argument(
        "-n",
        "--strips",
        type=int,
        default=40,
        help="number of vertical strips (default: 40)",
    )
    parser.add_argument(
        "-g",
        "--grayscale",
        action="store_true",
        help="convert the source to grayscale before processing",
    )
    args = parser.parse_args()

    if args.strips < 2:
        parser.error("--strips must be at least 2")
    if not args.input.is_file():
        parser.error(f"{args.input} does not exist")

    output = args.output or args.input.with_name(
        f"{args.input.stem}_glitch{args.input.suffix}"
    )
    try:
        with Image.open(args.input) as image:
            result = glitch(image, args.strips, args.grayscale)
    except UnidentifiedImageError:
        parser.error(f"{args.input} is not a readable image")
    result.save(output, quality=95)


if __name__ == "__main__":
    main()
