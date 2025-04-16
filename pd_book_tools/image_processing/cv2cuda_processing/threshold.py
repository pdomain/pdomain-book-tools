import cv2
import numpy as np


def cv2_binary_thresh_gpu(img_gpu: cv2.cuda.GpuMat, level=127) -> cv2.cuda.GpuMat:
    return cv2.cuda.threshold(img_gpu, level, 255, cv2.THRESH_BINARY)[1]


def cv2_convert_to_grayscale_gpu(img_gpu: cv2.cuda.GpuMat) -> cv2.cuda.GpuMat:
    return cv2.cuda.cvtColor(img_gpu, cv2.COLOR_BGR2GRAY)


def gpu_min_max(img_gpu: cv2.cuda.GpuMat) -> tuple:
    """
    Computes the min and max values of a GpuMat (image) on the GPU using reduction.
    Reduces across rows first, then across columns to get the global min/max values.

    Args:
        img_gpu (cv2.cuda.GpuMat): The input image on the GPU.

    Returns:
        tuple: A tuple containing the (min_value, max_value).
    """
    # First, reduce across columns (dim=1)
    min_val_col_gpu = cv2.cuda.GpuMat()
    max_val_col_gpu = cv2.cuda.GpuMat()
    cv2.cuda.reduce(img_gpu, min_val_col_gpu, 1, cv2.REDUCE_MIN, cv2.CV_32F)
    cv2.cuda.reduce(img_gpu, max_val_col_gpu, 1, cv2.REDUCE_MAX, cv2.CV_32F)

    min_val_gpu = cv2.cuda.GpuMat()
    max_val_gpu = cv2.cuda.GpuMat()
    cv2.cuda.reduce(img_gpu, min_val_gpu, 0, cv2.REDUCE_MIN, cv2.CV_32F)
    cv2.cuda.reduce(img_gpu, max_val_gpu, 0, cv2.REDUCE_MAX, cv2.CV_32F)

    # Download the result back to CPU as scalar values
    min_val = min_val_gpu.download()[0]  # Get the single value from the result
    max_val = max_val_gpu.download()[0]  # Get the single value from the result

    return min_val, max_val


def otsu_binary_thresh(img_gpu: cv2.cuda.GpuMat) -> cv2.cuda.GpuMat:
    """
    Performs Otsu's thresholding on an OpenCV CUDA GpuMat array (uint8 input, grayscale).

    Args:
        img_gpu (cv2.cuda.GpuMat): Input image (uint8, grayscale, on the GPU).

    Returns:
        cv2.cuda.GpuMat: Thresholded binary image (on the GPU, as uint8).
    """
    # Convert the image to float32 for processing
    img_gpu_float32 = cv2.cuda.GpuMat()
    img_gpu.convertTo(rtype=cv2.CV_32F, alpha=1.0 / 255.0, dst=img_gpu)

    # Compute the histogram using OpenCV CUDA
    min_val, max_val = gpu_min_max(img_gpu_float32)

    hist_gpu = cv2.cuda.histCalc(img_gpu_float32, bins=256, range=(min_val, max_val))

    # Compute the histogram bin centers (CPU side)
    bin_centers = np.linspace(min_val, max_val, 256)

    # Get cumulative sums and means (all on GPU)
    weight1_gpu = cv2.cuda.cumsum(hist_gpu)
    weight2_gpu = weight1_gpu[-1] - weight1_gpu
    mean1_gpu = cv2.cuda.cumsum(hist_gpu * bin_centers) / (weight1_gpu + 1e-7)
    mean2_gpu = (
        cv2.cuda.cumsum(hist_gpu[::-1] * bin_centers[::-1]) / (weight2_gpu[::-1] + 1e-7)
    )[::-1]

    # Compute the between-class variance (GPU side)
    between_class_variance_gpu = (
        weight1_gpu[:-1] * weight2_gpu[1:] * (mean1_gpu[:-1] - mean2_gpu[1:]) ** 2
    )

    # Get the Otsu threshold (index with max variance)
    otsu_threshold_gpu = bin_centers[:-1][cv2.cuda.max(between_class_variance_gpu)]

    # Convert to uint8 right before thresholding (for correct thresholding behavior)
    img_gpu_uint8 = cv2.cuda.GpuMat()
    img_gpu_float32.convertTo(rtype=cv2.CV_32F, alpha=255.0, dst=img_gpu_uint8)

    # Apply binary thresholding (GPU side)
    binary_img_gpu = cv2.cuda.threshold(
        img_gpu_uint8, otsu_threshold_gpu, 255, cv2.THRESH_BINARY
    )[1]

    # Return the binary image as a GpuMat (still on the GPU)
    return binary_img_gpu
