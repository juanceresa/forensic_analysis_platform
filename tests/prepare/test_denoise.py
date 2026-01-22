"""Tests for denoise module."""

import pytest
import numpy as np
import cv2
from farmer_factory.prepare.triage import DocumentPath


def test_bilateral_filter():
    """Test bilateral filtering for typed documents."""
    # Create noisy image
    clean = np.ones((100, 100), dtype=np.uint8) * 200
    noise = np.random.randint(-20, 20, (100, 100), dtype=np.int16)
    noisy = np.clip(clean.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    from farmer_factory.prepare.denoise import denoise_bilateral
    denoised = denoise_bilateral(noisy)

    # Check output is smoother (lower variance)
    assert np.std(denoised) < np.std(noisy)
    # Check dimensions preserved
    assert denoised.shape == noisy.shape


def test_nlmeans_filter():
    """Test non-local means filtering for handwritten documents."""
    # Create noisy image
    clean = np.ones((100, 100), dtype=np.uint8) * 180
    noise = np.random.randint(-30, 30, (100, 100), dtype=np.int16)
    noisy = np.clip(clean.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    from farmer_factory.prepare.denoise import denoise_nlmeans
    denoised = denoise_nlmeans(noisy)

    # Check output is smoother (lower variance)
    assert np.std(denoised) < np.std(noisy)
    # Check dimensions preserved
    assert denoised.shape == noisy.shape


def test_denoise_dispatch_typed():
    """Test denoise dispatches to bilateral for TYPED path."""
    noisy = np.ones((100, 100), dtype=np.uint8) * 200

    from farmer_factory.prepare.denoise import denoise
    denoised = denoise(noisy, DocumentPath.TYPED)

    # Just check it runs and returns same shape
    assert denoised.shape == noisy.shape


def test_denoise_dispatch_handwritten():
    """Test denoise dispatches to NLMeans for HANDWRITTEN path."""
    noisy = np.ones((100, 100), dtype=np.uint8) * 180

    from farmer_factory.prepare.denoise import denoise
    denoised = denoise(noisy, DocumentPath.HANDWRITTEN)

    # Just check it runs and returns same shape
    assert denoised.shape == noisy.shape
