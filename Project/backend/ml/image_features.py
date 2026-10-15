"""Características clásicas de imagen (sin redes neuronales) para retina y radiografías.

Se usan descriptores simples y explicables: estadísticas por canal, histograma de intensidad,
textura (LBP) y contenido de bordes. Es una línea base: con pocos cientos de imágenes y sin
pesos preentrenados no se puede esperar rendimiento clínico.
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageOps
from skimage.feature import local_binary_pattern
from skimage.filters import sobel

SIZE = 256  # lado del recorte cuadrado al que se normaliza cada imagen
MAX_PIXELS = 40_000_000  # defensa contra "bombas de descompresión"

Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class ImageError(ValueError):
    """El archivo no es una imagen válida o es inadecuada."""


def load_image(data: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()  # detecta archivos corruptos sin decodificar todo
        img = Image.open(io.BytesIO(data))  # verify() deja el objeto inservible: reabrir
        img = ImageOps.exif_transpose(img).convert("RGB")
    except Exception as exc:  # noqa: BLE001 - cualquier fallo de decodificación es "imagen inválida"
        raise ImageError("El archivo no es una imagen válida (usa JPG o PNG).") from exc
    if min(img.size) < 64:
        raise ImageError("La imagen es demasiado pequeña (mínimo 64 píxeles por lado).")
    return img


def _prepare(img: Image.Image) -> np.ndarray:
    return np.asarray(ImageOps.fit(img, (SIZE, SIZE), Image.Resampling.BILINEAR), dtype=np.float32) / 255.0


FEATURE_NAMES = (
    [f"{c}_{s}" for c in "rgb" for s in ("mean", "std", "p5", "p95")]
    + [f"hist_{i}" for i in range(8)]
    + [f"lbp_{i}" for i in range(10)]
    + ["edge_mean", "edge_p95", "bright_frac", "dark_frac"]
)


def extract(img: Image.Image) -> np.ndarray:
    a = _prepare(img)
    feats: list[float] = []
    for ch in range(3):
        c = a[..., ch]
        feats += [c.mean(), c.std(), np.percentile(c, 5), np.percentile(c, 95)]
    gray = a.mean(axis=2)
    hist, _ = np.histogram(gray, bins=8, range=(0, 1), density=True)
    feats += (hist / (hist.sum() + 1e-9)).tolist()
    lbp = local_binary_pattern((gray * 255).astype(np.uint8), P=8, R=1, method="uniform")
    lh, _ = np.histogram(lbp, bins=10, range=(0, 10), density=True)
    feats += (lh / (lh.sum() + 1e-9)).tolist()
    edges = sobel(gray)
    feats += [edges.mean(), np.percentile(edges, 95), float((gray > 0.8).mean()), float((gray < 0.1).mean())]
    return np.asarray(feats, dtype=np.float64)
