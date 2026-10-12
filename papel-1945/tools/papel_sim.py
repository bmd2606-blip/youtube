"""Simulador 2.5D de papel que se arruga / se despliega.

Genera fotogramas 1920x1080 sobre negro puro a partir de la textura plana de la hoja.

    python3 -I tools/papel_sim.py unfold  <textura.png> <carpeta_salida>
    python3 -I tools/papel_sim.py crumple <textura.png> <carpeta_salida>

La hoja plana ocupa 1200x780 px en (360, 150). Con k=0 el fotograma es idéntico a la
textura plana colocada en esa posición, así que enlaza sin saltos con la parte HTML.
"""
import math
import os
import sys

import cv2
import numpy as np

W, H = 1920, 1080
SW, SH = 1200, 780
SX, SY = 360, 150
FPS = 30
rng = np.random.default_rng(45)


# ---------- Campo de pliegues fuertes (espacio de la hoja) ----------
def crease_field(n, wmin, wmax, amin, amax, lmin=150, lmax=600):
    y, x = np.mgrid[0:SH, 0:SW].astype(np.float32)
    h = np.zeros((SH, SW), np.float32)
    for _ in range(n):
        px, py = rng.uniform(0, SW), rng.uniform(0, SH)
        a = rng.uniform(0, np.pi)
        d = (x - px) * np.cos(a) + (y - py) * np.sin(a)
        # pliegue afilado (perfil triangular) que se apaga lejos de la línea
        t = -(x - px) * np.sin(a) + (y - py) * np.cos(a)  # posición a lo largo del pliegue
        width = rng.uniform(wmin, wmax)
        length = rng.uniform(lmin, lmax)
        amp = rng.uniform(amin, amax) * (1 if rng.random() < 0.5 else -1)
        h += amp * np.clip(1 - np.abs(d) / width, 0, 1) * np.exp(-((t / length) ** 2))
    h -= cv2.GaussianBlur(h, (0, 0), 120)  # quitar inclinación global
    return h


def smooth_noise(shape, cells, seed):
    r = np.random.default_rng(seed)
    g = r.normal(0, 1, (cells[1], cells[0])).astype(np.float32)
    return cv2.resize(g, shape, interpolation=cv2.INTER_CUBIC)


CREASES = crease_field(220, 50, 200, 4, 12, 120, 420)
FINE = crease_field(600, 10, 40, 1.0, 3.0, 40, 140)
DX = smooth_noise((W, H), (9, 6), 1)
DY = smooth_noise((W, H), (9, 6), 2)
ANG_PH = rng.uniform(0, 2 * np.pi, 8)
ANG_AMP = np.array([0, 0, 0.06, 0.05, 0.045, 0.04, 0.035, 0.03, 0.025, 0.02, 0.02, 0.015, 0.015, 0.012])
ANG_PH = rng.uniform(0, 2 * np.pi, 14)
# Facetas propias de la bola (espacio local de la bola, 800x800 centrado)
def ball_field():
    y, x = np.mgrid[-400:400, -400:400].astype(np.float32)
    h = np.zeros((800, 800), np.float32)
    for _ in range(420):
        px, py = rng.uniform(-200, 200, 2)
        a = rng.uniform(0, np.pi)
        d = (x - px) * np.cos(a) + (y - py) * np.sin(a)
        t = -(x - px) * np.sin(a) + (y - py) * np.cos(a)
        width = rng.uniform(8, 40)
        length = rng.uniform(25, 90)
        amp = rng.uniform(2, 7) * (1 if rng.random() < 0.5 else -1)
        h += amp * np.clip(1 - np.abs(d) / width, 0, 1) * np.exp(-((t / length) ** 2))
    return h - cv2.GaussianBlur(h, (0, 0), 80)


BALLF = ball_field()
LIGHT = np.array([-0.45, -0.6, 0.9], np.float32)
LIGHT /= np.linalg.norm(LIGHT)


def render(tex, k, cx, cy, rot, ball):
    """k: 0 plano → 1 bola. (cx, cy): centro de la hoja en pantalla. rot: grados.
    ball: tamaño de la bola respecto a la hoja (p.ej. 0.24)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    qx, qy = xx - cx, yy - cy
    th = math.radians(rot)
    rx = qx * math.cos(th) + qy * math.sin(th)
    ry = -qx * math.sin(th) + qy * math.cos(th)

    # escala no uniforme: contorno irregular, más pequeño cuanto más arrugado
    e = k ** 0.9
    phi = np.arctan2(ry, rx)
    lump = np.zeros_like(phi)
    for i in range(2, 14):
        lump += ANG_AMP[i] * np.sin(i * phi + ANG_PH[i])
    # la bola es redonda: radio "ball" en px, igual en los dos ejes
    sx = (1 - e) + e * (ball / (SW / 2)) * (1 + lump)
    sy = (1 - e) + e * (ball / (SH / 2)) * (1 + lump)
    s = np.sqrt(sx * sy)
    u = rx / sx + SW / 2
    v = ry / sy + SH / 2
    # al cerrarse en bola, la hoja se recoge en un disco (mapa cuadrado → círculo)
    wr = float(np.clip((e - 0.8) / 0.2, 0, 1)) ** 2
    outside_fade = None
    if wr > 0.001:
        R = ball * (1 + lump)
        a = rx / R
        b = ry / R
        rad = np.sqrt(a * a + b * b)
        sc = 1 / np.maximum(rad, 1.0)  # fuera del disco: proyectar al borde (mapa continuo)
        a, b = a * sc, b * sc
        a2, b2, r2 = a * a, b * b, 2 * math.sqrt(2)
        t1 = np.clip(2 + a2 - b2, 0, None)
        t2 = np.clip(2 - a2 + b2, 0, None)
        sqx = 0.5 * np.sqrt(np.clip(t1 + r2 * a, 0, None)) - 0.5 * np.sqrt(np.clip(t1 - r2 * a, 0, None))
        sqy = 0.5 * np.sqrt(np.clip(t2 + r2 * b, 0, None)) - 0.5 * np.sqrt(np.clip(t2 - r2 * b, 0, None))
        u = u * (1 - wr) + (sqx * SW / 2 + SW / 2) * wr
        v = v * (1 - wr) + (sqy * SH / 2 + SH / 2) * wr
        # el papel fuera del disco se recoge (desaparece) de forma gradual
        outside_fade = 1 - wr * np.clip((rad - 1.0) / 0.02, 0, 1)
    # el papel se amontona de forma irregular
    u += k * 22 * DX
    v += k * 22 * DY

    mapx, mapy = u.astype(np.float32), v.astype(np.float32)
    rgb = cv2.remap(tex, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0).astype(np.float32)
    alpha = cv2.remap(np.ones((SH, SW), np.float32), mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    if outside_fade is not None:
        alpha *= outside_fade

    if k > 0.001:
        # relieve en pantalla: pliegues + bombeo de bola, más marcados al comprimir
        hh = cv2.remap(CREASES + FINE * (k**1.5) * 1.4, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE) * k * 0.55
        # al cerrarse en bola dominan las facetas propias de la bola (sin rayas radiales)
        wb = e**4
        if wb > 0.01:
            hb = cv2.remap(BALLF, (rx + 400).astype(np.float32), (ry + 400).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            hh = hh * (1 - 0.8 * wb) + hb * wb
        gy, gx = np.gradient(hh)
        n = np.dstack([-gx, -gy, np.ones_like(gx)])
        n /= np.linalg.norm(n, axis=2, keepdims=True)
        lam = (n @ LIGHT) / LIGHT[2]
        spec = np.clip(n @ (LIGHT + np.array([0, 0, 1], np.float32)) / np.linalg.norm(LIGHT + np.array([0, 0, 1])), 0, 1) ** 40
        lap = cv2.Laplacian(hh, cv2.CV_32F, ksize=5)
        ao = 1 - np.clip(lap * 0.015, 0, 0.45)  # sombra en los valles
        shade = np.clip(lam, 0.38, 1.22) * ao
        # volumen de bola: bordes más oscuros cuando está muy arrugado
        rn = np.clip(np.sqrt((rx / (SW / 2 * sx)) ** 2 + (ry / (SH / 2 * sy)) ** 2), 0, 1)
        sphere = 0.55 + 0.45 * np.sqrt(np.clip(1 - rn**2, 0, 1))
        shade *= (1 - e**6) + e**6 * sphere
        rgb = rgb * shade[..., None] + (spec * 35 * k)[..., None]

    # borde de la hoja suavizado y fondo negro puro
    out = rgb * alpha[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_in(t):
    return t**3


def main():
    mode, tex_path, out_dir = sys.argv[1:4]
    tex = cv2.imread(tex_path, cv2.IMREAD_COLOR)
    tex = cv2.resize(tex, (SW, SH))
    os.makedirs(out_dir, exist_ok=True)
    C0 = (SX + SW / 2, SY + SH / 2)
    BALL = 160  # radio de la bola en px
    frames = []
    if mode == "unfold":
        # 0.0–0.5 s: la bola cae y rebota · 0.5–1.9 s: se despliega
        n_fall, n_unf = 15, 42
        for i in range(n_fall):
            t = (i + 1) / n_fall
            y = -650 * (1 - t**2) if t < 0.8 else -40 * math.sin((t - 0.8) / 0.2 * math.pi)
            frames.append((1.0, C0[0], C0[1] + y, -40 + 30 * t, BALL))
        for i in range(n_unf):
            t = (i + 1) / n_unf
            k = 1 - ease_out(t)
            wob = 3 * math.sin(t * 9) * (1 - t)
            frames.append((k, C0[0], C0[1], -10 * (1 - ease_out(t)) + wob, BALL))
    else:
        # 0.0–0.9 s: se arruga · 0.9–1.4 s: la bola sale lanzada
        n_cr, n_out = 27, 15
        for i in range(n_cr):
            t = (i + 1) / n_cr
            k = ease_in(t) * 0.6 + t * 0.4
            frames.append((k, C0[0], C0[1], -22 * ease_in(t) + 2 * math.sin(t * 10) * t, BALL))
        for i in range(n_out):
            t = (i + 1) / n_out
            frames.append((1.0, C0[0] + 1500 * t**2, C0[1] + 200 * t**2 - 120 * math.sin(t * math.pi), -22 - 260 * t, BALL))
    for i, f in enumerate(frames):
        cv2.imwrite(os.path.join(out_dir, f"f{i:04d}.png"), render(tex, *f))
    print(mode, len(frames), "frames")


if __name__ == "__main__":
    main()
