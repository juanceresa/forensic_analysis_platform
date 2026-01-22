"""Denoise module for noise reduction."""

import cv2
import numpy as np
from .triage import DocumentPath


def denoise_bilateral(image: np.ndarray) -> np.ndarray:
    """
    Apply bilateral filter for edge-preserving smoothing.
    Used for typed documents to reduce noise while preserving text edges.

    Args:
        image: Grayscale image (H x W)

    Returns:
        Denoised image
    """
    # Bilateral filter: d=5, sigmaColor=50, sigmaSpace=50
    return cv2.bilateralFilter(image, d=5, sigmaColor=50, sigmaSpace=50)


def denoise_nlmeans(image: np.ndarray) -> np.ndarray:
    """
    Apply non-local means denoising.
    Used for handwritten documents with complex textures.

    Args:
        image: Grayscale image (H x W)

    Returns:
        Denoised image
    """
    # Non-local means: h=10, templateWindowSize=7, searchWindowSize=21
    return cv2.fastNlMeansDenoising(image, h=10, templateWindowSize=7, searchWindowSize=21)


def denoise(image: np.ndarray, path: DocumentPath) -> np.ndarray:
    """
    Denoise image based on document path.

    Args:
        image: Grayscale image (H x W)
        path: Document processing path

    Returns:
        Denoised image
    """
    if path == DocumentPath.TYPED:
        return denoise_bilateral(image)
    else:  # HANDWRITTEN
        return denoise_nlmeans(image)
