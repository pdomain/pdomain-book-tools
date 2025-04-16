# Configure logging
import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def find_and_draw_contours(img: np.array):
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # TODO: Optimize the rectangle drawing by using Numpy
    if contours:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(img, (x, y), (x + w, y + h), (125, 255, 0), 4)

    return img, contours


def remove_small_contours(
    img: np.ndarray,
    contours,
    min_w_pct: float = 0.04,
    min_w_pixels: int = 5,
    min_h_pct: float = 0.03,
    min_h_pixels: int = 5,
    small_contour_w: int = 10,
    small_contour_h: int = 10,
    nearby_pixel_count: int = 10,
):
    """
    Remove small or isolated contours from a grayscale image.

    For each contour:
      - If both width and height are extremely small (<10 pixels by default), remove it.
      - Otherwise, if the contour is below a size threshold (relative to the image),
        compute a search area around it. If the sum of the surrounding pixels (after
        zeroing the contour area) is below a threshold, the contour is removed.

    Returns:
      - The modified image.
      - A BGR visualization image with green rectangles indicating removal and red
        rectangles where contours were retained.
    """
    # Create a visualization image (in BGR) from a copy of the grayscale image.
    contour_search_img = cv2.cvtColor(img.copy(), cv2.COLOR_GRAY2BGR)

    if not contours:
        return img, contour_search_img

    img_h, img_w = img.shape[:2]
    pixels_w = max(int(img_w * min_w_pct), min_w_pixels)
    pixels_h = max(int(img_h * min_h_pct), min_h_pixels)
    threshold_sum = 255 * nearby_pixel_count  # constant threshold for nearby pixels

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        # Grab the region corresponding to the contour.
        contour_region = img[y : y + h, x : x + w]
        contour_sum = np.sum(contour_region)
        # Skip if the contour area is already zeroed out.
        if contour_sum == 0:
            continue

        # Directly remove small contours.
        if w < small_contour_w and h < small_contour_h:
            img[y : y + h, x : x + w] = 0
            continue

        # Process contours below size thresholds.
        if w < pixels_w and h < pixels_h:
            # Define a search area around the contour.
            minX = max(0, int(x - pixels_w * 0.75))
            maxX = min(img_w, int(x + w + pixels_w * 0.75))
            minY = max(0, int(y - pixels_h * 0.5))
            maxY = min(img_h, int(y + h + pixels_h * 0.5))

            search_region = img[minY:maxY, minX:maxX]
            # Calculate what the sum would be if the contour were removed.
            search_sum = np.sum(search_region) - contour_sum

            if search_sum < threshold_sum:
                # Remove the contour (set the region to zeros) if not enough nearby pixels.
                img[y : y + h, x : x + w] = 0
                cv2.rectangle(
                    contour_search_img, (minX, minY), (maxX, maxY), (0, 255, 0), 1
                )
            else:
                cv2.rectangle(
                    contour_search_img, (minX, minY), (maxX, maxY), (0, 0, 255), 1
                )

    return img, contour_search_img
