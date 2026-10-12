"""Genera la textura de papel arrugado (pliegues facetados + grano) en assets/papel.png."""
import sys
import numpy as np
from PIL import Image, ImageFilter

W, H = 1200, 780
rng = np.random.default_rng(1945)
y, x = np.mgrid[0:H, 0:W].astype(np.float32)

# Pliegues: suma de "crestas" a lo largo de rectas aleatorias → superficie facetada
h = np.zeros((H, W), np.float32)
for _ in range(110):
    px, py = rng.uniform(0, W), rng.uniform(0, H)
    ang = rng.uniform(0, np.pi)
    nx, ny = np.cos(ang), np.sin(ang)
    d = (x - px) * nx + (y - py) * ny
    amp = rng.uniform(0.004, 0.02) * (1 if rng.random() < 0.55 else -1)
    h += amp * np.abs(d)
# grano fino del papel
noise = rng.normal(0, 1, (H, W)).astype(np.float32)
noise_img = Image.fromarray(((noise - noise.min()) / np.ptp(noise) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
h += (np.asarray(noise_img, np.float32) / 255 - 0.5) * 1.6

# Iluminación lambertiana
gy, gx = np.gradient(h)
nz = np.ones_like(h)
norm = np.sqrt(gx**2 + gy**2 + nz**2)
L = np.array([-0.55, -0.65, 0.9]); L /= np.linalg.norm(L)
shade = (-gx * L[0] - gy * L[1] + nz * L[2]) / norm
# contraste normalizado: pliegues visibles pero suaves
shade = (shade - shade.mean()) / (shade.std() + 1e-6) * 0.055 + 1.0
shade = np.clip(shade, 0.84, 1.1)

# Color de papel envejecido con viñeta y manchas suaves
base = np.array([236, 224, 198], np.float32)
vign = 1 - 0.18 * (((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
stain = Image.fromarray((rng.random((H // 40, W // 40)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(30))
stain = np.asarray(stain, np.float32) / 255
tint = np.stack([1 - 0.03 * stain, 1 - 0.06 * stain, 1 - 0.12 * stain], -1)
rgb = base * shade[..., None] * vign[..., None] * tint
Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(sys.argv[1])
print("ok", sys.argv[1])
