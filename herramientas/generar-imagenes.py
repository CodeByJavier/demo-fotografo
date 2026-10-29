#!/usr/bin/env python3
"""
Genera la fotografía de la plantilla de fotógrafo (paisaje y viaje).

Desde el entorno donde se creó la plantilla no había acceso a bancos de
imágenes, así que las fotos se construyen por código. Hay cinco "motivos":
montaña con niebla, costa, bosque con niebla, cielo nocturno y luz de
ventana. Cada foto se guarda en dos tamaños:
  - nombre.jpg      → lado largo de 1600 px, para el visor a pantalla completa
  - nombre-800.jpg  → lado largo de 800 px, para las miniaturas de la galería
La página elige cuál descargar con srcset/sizes.

Uso:  python herramientas/generar-imagenes.py   (desde la carpeta del proyecto)

Para usar fotos reales del cliente basta con sustituir los archivos con el
mismo nombre. Si la proporción cambia, hay que actualizar width/height en el
HTML para que el navegador reserve el hueco correcto.
"""
import os
import numpy as np
from PIL import Image, ImageFilter, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "img")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(20261029)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def to_img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def vgrad(w, h, top, bottom, gamma=1.0):
    t = (np.linspace(0, 1, h) ** gamma)[:, None, None]
    col = np.array(top, float)[None, None, :] * (1 - t) + np.array(bottom, float)[None, None, :] * t
    return np.broadcast_to(col, (h, w, 3)).copy()  # copia real: luego se modifica in situ


def profile(w, waves=6, seed=0, rough=1.0):
    """Perfil 1D suave (suma de senos) normalizado a 0..1."""
    r = np.random.default_rng(seed)
    x = np.linspace(0, 1, w)
    y = np.zeros(w)
    for k in range(waves):
        f = r.uniform(0.6, 4.5) * (k + 1) * 0.5 * rough
        y += r.uniform(0.25, 1.0) / (k + 1) * np.sin(2 * np.pi * f * x + r.uniform(0, 6.28))
    y -= y.min()
    return y / y.max() if y.max() > 0 else y


def blur(mask, radius):
    im = Image.fromarray(np.clip(mask * 255, 0, 255).astype(np.uint8))
    return np.array(im.filter(ImageFilter.GaussianBlur(radius)), float) / 255.0


def grain(arr, amount=6.0):
    h, w = arr.shape[:2]
    return arr + rng.normal(0, amount, (h, w, 1))


def vignette(arr, strength=0.32):
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    return arr * (1 - strength * np.clip((d - 0.45) / 1.05, 0, 1) ** 1.7)[:, :, None]


def glow(arr, cx, cy, radius, color, amount):
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / radius
    g = np.clip(1 - d, 0, 1) ** 2.4
    return arr + g[:, :, None] * (np.array(color, float)[None, None, :] - arr) * amount


def finish(arr, grain_amt=6.0, vig=0.3):
    return to_img(vignette(grain(arr, grain_amt), vig))


# ---------------------------------------------------------------------------
# Motivos
# ---------------------------------------------------------------------------
PALETTES = {
    # cielo arriba, cielo horizonte, cresta lejana, cresta cercana, halo
    "dawn": ((92, 106, 122), (238, 203, 168), (150, 156, 152), (30, 36, 32), (255, 224, 178)),
    "mist": ((176, 186, 188), (232, 231, 223), (140, 150, 142), (44, 52, 45), (250, 248, 238)),
    "dusk": ((54, 62, 78), (206, 148, 108), (108, 106, 104), (22, 25, 24), (255, 190, 130)),
    "forest": ((150, 166, 160), (226, 226, 210), (120, 136, 118), (28, 38, 30), (243, 243, 225)),
    "blue": ((38, 56, 82), (150, 172, 190), (92, 108, 122), (16, 22, 28), (210, 226, 236)),
}


def mountains(w, h, palette="mist", layers=6, sun=(0.6, 0.25), seed=0, horizon=0.55):
    sky_top, sky_hz, far, near, halo = PALETTES[palette]
    hz = int(h * horizon)
    arr = np.empty((h, w, 3))
    arr[:hz] = vgrad(w, hz, sky_top, sky_hz, 1.5)
    arr[hz:] = np.array(sky_hz, float)
    arr = glow(arr, sun[0] * w, sun[1] * h, 0.75 * w, halo, 0.75)
    yy = np.mgrid[0:h, 0:w][0]
    for i in range(layers):
        t = i / max(1, layers - 1)
        base = int(hz + (h - hz) * (0.06 + 0.85 * t))
        top = base - (profile(w, 5 + i, seed * 31 + i) * (0.16 - 0.10 * t) * h).astype(int)
        col = np.array(far) * (1 - t) + np.array(near) * t
        col = col * (1 - 0.55 * (1 - t)) + np.array(sky_hz) * 0.55 * (1 - t)
        m = blur((yy >= top[None, :]).astype(float), 1.2)
        arr = arr * (1 - m[:, :, None]) + col[None, None, :] * m[:, :, None]
        band = np.clip(1 - np.abs(yy - top[None, :]) / (0.045 * h), 0, 1) ** 2
        arr += band[:, :, None] * (np.array(sky_hz) - arr) * 0.3 * (1 - t)
    return finish(arr)


def seascape(w, h, palette="dawn", sun=(0.62, 0.36), seed=0, horizon=0.56, rocks=True):
    """Mar abierto con reflejo del sol y, opcionalmente, islotes a contraluz."""
    r = np.random.default_rng(seed)
    sky_top, sky_hz, _, near, halo = PALETTES[palette]
    hz = int(h * horizon)
    arr = np.empty((h, w, 3))
    arr[:hz] = vgrad(w, hz, sky_top, sky_hz, 1.6)

    # Agua: más oscura hacia abajo, con el color del cielo reflejado
    water_top = np.array(sky_hz) * 0.82
    water_bot = np.array(sky_top) * 0.55
    arr[hz:] = vgrad(w, h - hz, water_top, water_bot, 0.8)

    sx, sy = sun[0] * w, sun[1] * h
    arr = glow(arr, sx, sy, 0.6 * w, halo, 0.8)

    # Estela del sol sobre el agua: columna brillante rota por líneas horizontales
    yy, xx = np.mgrid[0:h, 0:w]
    below = yy >= hz
    width = 0.05 * w + (yy - hz).clip(0) * 0.35
    col = np.exp(-((xx - sx) ** 2) / (2 * width ** 2 + 1e-6))
    ripples = (np.sin(yy * 0.9 + r.uniform(0, 6)) * 0.5 + 0.5) * (r.random((h, 1)) > 0.35)
    streak = col * ripples * below * np.exp(-(yy - hz).clip(0) / (0.55 * h))
    streak = np.array(Image.fromarray((np.clip(streak, 0, 1) * 255).astype(np.uint8)).filter(
        ImageFilter.BoxBlur(2)), float) / 255.0
    arr += streak[:, :, None] * (np.array(halo) - arr) * 0.85

    # Oleaje: bandas horizontales que se ensanchan hacia la orilla
    depth = ((yy - hz).clip(0) / max(1, h - hz)) ** 1.4
    waves = np.sin(yy * (0.35 - 0.25 * depth) + np.sin(xx * 0.004 + r.uniform(0, 6)) * 3)
    arr += (waves * depth * below)[:, :, None] * 9

    # Línea de horizonte nítida
    arr[hz - 1:hz + 1] = arr[hz - 1:hz + 1] * 0.92 + np.array(sky_hz) * 0.08

    if rocks:
        # Un par de islotes/farallones a contraluz sobre el horizonte
        for k in range(r.integers(1, 3)):
            cx = r.uniform(0.1, 0.9) * w
            rw = r.uniform(0.12, 0.26) * w
            rh = r.uniform(0.035, 0.075) * h
            # Perfil suave con laderas empinadas, como un farallón
            p = profile(int(rw), 3, seed * 7 + k, rough=0.6)
            env = np.sin(np.linspace(0, np.pi, int(rw))) ** 0.35
            heights = (p * 0.35 + 0.65) * env * rh
            x0 = int(cx - rw / 2)
            m = np.zeros((h, w))
            for i, hh in enumerate(heights):
                x = x0 + i
                if 0 <= x < w:
                    m[int(hz - hh):hz + 2, x] = 1
            m = blur(m, 1.0)
            # Un poco de bruma marina: el islote no es negro puro
            rock = np.array(near) * 0.78 + np.array(sky_hz) * 0.22
            arr = arr * (1 - m[:, :, None]) + rock[None, None, :] * m[:, :, None]
    return finish(arr, 5.5, 0.34)


def forest(w, h, palette="forest", seed=0, rays=True):
    """Troncos verticales que se pierden en la niebla, con rayos de luz."""
    r = np.random.default_rng(seed)
    sky_top, sky_hz, far, near, halo = PALETTES[palette]
    arr = vgrad(w, h, np.array(sky_hz) * 0.92, np.array(far) * 0.85, 1.0)
    yy, xx = np.mgrid[0:h, 0:w]

    layers = 5
    for i in range(layers):
        t = i / (layers - 1)
        fog = 0.82 * (1 - t) ** 1.3
        col = np.array(near) * (1 - fog) + np.array(sky_hz) * fog
        n = int(r.integers(5, 9) + (1 - t) * 6)
        m = np.zeros((h, w))
        for _ in range(n):
            cx = r.uniform(-0.05, 1.05) * w
            tw = (0.006 + 0.03 * t ** 1.6) * w * r.uniform(0.6, 1.4)
            lean = r.uniform(-0.03, 0.03) * w
            x_at = cx + lean * (yy / h)
            width_at = tw * (1 + 0.25 * (yy / h))
            m = np.maximum(m, (np.abs(xx - x_at) < width_at / 2).astype(float))
            # alguna rama inclinada en los árboles cercanos
            if t > 0.5 and r.random() < 0.35:
                by = r.uniform(0.12, 0.45) * h
                dirn = r.choice([-1, 1])
                length = r.uniform(0.04, 0.09) * w
                for s in np.linspace(0, 1, 120):
                    px = int(cx + dirn * s * length)
                    py = int(by - s * length * 1.1)
                    bw = max(1, int(tw * 0.12 * (1 - s) + 1))
                    if 0 <= py < h:
                        m[max(0, py - bw):py + bw, max(0, px - bw):max(0, px + bw)] = 1
        m = blur(m, 0.9 + (1 - t) * 2.2)
        arr = arr * (1 - m[:, :, None]) + col[None, None, :] * m[:, :, None]
        # niebla entre capas
        arr = arr * (1 - 0.10 * (1 - t)) + np.array(sky_hz) * 0.10 * (1 - t)

    # Suelo con musgo, más oscuro abajo
    ground = np.clip((yy / h - 0.82) / 0.18, 0, 1) ** 1.5
    arr = arr * (1 - ground[:, :, None] * 0.55) + np.array(near)[None, None, :] * ground[:, :, None] * 0.55

    if rays:
        # Haces de luz diagonales desde la esquina superior
        ang = r.uniform(0.35, 0.6)
        u = (xx * np.cos(ang) + yy * np.sin(ang)) / w
        beams = (np.sin(u * r.uniform(14, 22)) * 0.5 + 0.5) ** 6
        fade = np.clip(1 - yy / (0.9 * h), 0, 1) * np.clip(1 - xx / (1.1 * w), 0, 1)
        arr += (beams * fade)[:, :, None] * (np.array(halo) - arr) * 0.35
    return finish(arr, 6.5, 0.36)


def octave_noise(h, w, r, scales=((48, 0.55), (16, 0.3), (5, 0.15))):
    """Ruido en varias escalas: da textura de nube en vez de una mancha lisa."""
    n = np.zeros((h, w))
    for radius, weight in scales:
        layer = blur(r.random((h, w)), radius)
        layer = (layer - layer.min()) / (layer.max() - layer.min() + 1e-9)
        n += layer * weight
    return n


def night(w, h, seed=0, milky=True, horizon=0.8, warm_glow=True, meteors=0):
    """Cielo estrellado con Vía Láctea, meteoros opcionales y silueta de montaña."""
    r = np.random.default_rng(seed)
    arr = vgrad(w, h, (5, 8, 18), (30, 40, 64), 1.3)
    yy, xx = np.mgrid[0:h, 0:w]
    band = np.zeros((h, w))

    if milky:
        ang = r.uniform(-1.15, -0.75)
        cx, cy = r.uniform(0.4, 0.6) * w, r.uniform(0.32, 0.48) * h
        across = (-(xx - cx) * np.sin(ang) + (yy - cy) * np.cos(ang)) / h
        along = ((xx - cx) * np.cos(ang) + (yy - cy) * np.sin(ang)) / h
        # Más ancha y brillante en el núcleo, se apaga hacia los extremos
        band = np.exp(-(across ** 2) / (2 * 0.12 ** 2)) * np.exp(-(along ** 2) / (2 * 0.55 ** 2))
        clouds = octave_noise(h, w, r)
        glowmap = np.clip(band * (clouds * 1.6 - 0.25), 0, 1)
        arr += glowmap[:, :, None] * np.array([96, 86, 100])[None, None, :]
        # Franjas de polvo oscuro dentro del núcleo
        dust = octave_noise(h, w, r, ((10, 0.6), (3, 0.4)))
        lanes = np.clip((dust - 0.55) * 4, 0, 1) * np.clip(band * 1.4 - 0.3, 0, 1)
        arr *= (1 - 0.55 * lanes)[:, :, None]

    # Estrellas: muchas débiles y pocas brillantes, más densas en la Vía Láctea
    n = int(w * h / 220)
    sx = r.integers(0, w, n)
    sy = r.integers(0, int(h * horizon), n)
    keep = r.random(n) < 0.45 + 0.55 * band[sy, sx]
    sx, sy = sx[keep], sy[keep]
    bright = np.clip(0.18 + r.exponential(0.2, sx.size), 0, 1)
    stars = np.zeros((h, w))
    stars[sy, sx] = bright
    big = bright > 0.62
    halo = np.zeros((h, w))
    halo[sy[big], sx[big]] = bright[big]
    stars = np.clip(stars + blur(halo, 1.4) * 9, 0, 1)
    tint = np.where(r.random((h, w, 1)) < 0.55, np.array([[[255, 238, 222]]]), np.array([[[212, 226, 255]]]))
    arr += stars[:, :, None] * (tint - arr)

    # Meteoros: trazos finos que se desvanecen
    if meteors:
        trail = np.zeros((h, w))
        for _ in range(meteors):
            x0, y0 = r.uniform(0.15, 0.85) * w, r.uniform(0.08, 0.45) * h
            a2 = r.uniform(0.35, 0.8) * r.choice([-1, 1])
            length = r.uniform(0.08, 0.2) * w
            for t in np.linspace(0, 1, int(length)):
                x = int(x0 + np.cos(a2) * length * t)
                y = int(y0 + np.sin(abs(a2)) * length * t)
                if 0 <= x < w and 0 <= y < h:
                    trail[y, x] = max(trail[y, x], (1 - t) ** 1.5)
        trail = np.clip(blur(trail, 0.7) * 2.2, 0, 1)
        arr += trail[:, :, None] * (np.array([240, 246, 255]) - arr)

    hz = int(h * horizon)
    if warm_glow:
        arr = glow(arr, r.uniform(0.2, 0.8) * w, hz, 0.7 * w, (110, 74, 62), 0.45)

    top = hz - (profile(w, 7, seed * 13, rough=1.3) * 0.13 * h).astype(int)
    m = blur((yy >= top[None, :]).astype(float), 0.8)
    arr = arr * (1 - m[:, :, None]) + np.array([5, 7, 9])[None, None, :] * m[:, :, None]
    return finish(arr, 4.0, 0.26)


def window_light(w, h, seed=1):
    """Luz de ventana sobre pared (para el "sobre mí", en blanco y negro)."""
    r = np.random.default_rng(seed)
    arr = vgrad(w, h, (176, 176, 172), (78, 78, 76), 1.15)
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w * r.uniform(0.4, 0.55), h * r.uniform(0.4, 0.55)
    ww, hh = w * 0.3, h * 0.42
    skew = r.uniform(-0.5, 0.5)
    u = (xx - cx) / ww + skew * (yy - cy) / hh
    v = (yy - cy) / hh
    patch = ((np.abs(u) < 1) & (np.abs(v) < 1)).astype(float)
    patch = np.clip(patch - (np.abs(u) < 0.06), 0, 1)
    patch = np.clip(patch - (np.abs(v) < 0.05), 0, 1)
    arr += blur(patch, w * 0.01)[:, :, None] * 92
    return finish(arr, 7, 0.45)


# ---------------------------------------------------------------------------
# Guardado
# ---------------------------------------------------------------------------
def mono(im, contrast=1.15):
    """Blanco y negro con algo más de contraste, como un revelado clásico."""
    g = ImageOps.grayscale(im)
    g = ImageOps.autocontrast(g, cutoff=0.5)
    arr = (np.array(g, float) - 128) * contrast + 128
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGB")


def save(im, name, thumb=True, quality=82):
    path = os.path.join(OUT, f"{name}.jpg")
    im.save(path, "JPEG", quality=quality, optimize=True, progressive=True)
    line = f"{name:22s} {im.width}x{im.height}  {os.path.getsize(path) // 1024:4d} KB"
    if thumb:
        t = im.copy()
        t.thumbnail((800, 800), Image.LANCZOS)
        tp = os.path.join(OUT, f"{name}-800.jpg")
        t.save(tp, "JPEG", quality=80, optimize=True, progressive=True)
        line += f"   + miniatura {t.width}x{t.height} {os.path.getsize(tp) // 1024} KB"
    print(line)


# Proporciones habituales en fotografía (lado largo 1600 px)
R32, R23, R45, R169, R11 = (1600, 1067), (1067, 1600), (1280, 1600), (1600, 900), (1400, 1400)

if __name__ == "__main__":
    # ---- Portada: pase de fotos (+ versión de 1000 px para móvil) ----
    for name, im in [
        ("portada-1", seascape(2000, 1250, "dusk", (0.66, 0.40), 3)),
        ("portada-2", mountains(2000, 1250, "mist", 7, (0.42, 0.22), 7, horizon=0.48)),
        ("portada-3", night(2000, 1250, 11, horizon=0.84)),
        ("portada-4", forest(2000, 1250, "forest", 5)),
    ]:
        save(im, name, thumb=False)
        small = im.copy()
        small.thumbnail((1000, 1000), Image.LANCZOS)
        small.save(os.path.join(OUT, f"{name}-1000.jpg"), "JPEG", quality=80, optimize=True, progressive=True)

    # ---- Galería por series ----
    save(seascape(*R32, "dusk", (0.70, 0.38), 21), "costa-fisterra")
    save(seascape(*R169, "dawn", (0.30, 0.34), 23, rocks=False), "costa-cies")
    save(mono(seascape(*R23, "mist", (0.5, 0.30), 25, horizon=0.5)), "costa-trece")
    save(seascape(*R45, "blue", (0.45, 0.30), 27, horizon=0.52), "costa-vilan")

    save(mono(mountains(*R32, "mist", 7, (0.5, 0.2), 31)), "montana-ancares")
    save(mountains(*R23, "dawn", 7, (0.6, 0.18), 33, horizon=0.42), "montana-ribeira")
    save(mountains(*R169, "forest", 6, (0.3, 0.22), 35), "montana-courel")
    save(mountains(*R11, "dusk", 6, (0.55, 0.3), 37, horizon=0.5), "montana-capelada")

    save(forest(*R23, "forest", 41), "bosque-eume")
    save(forest(*R32, "mist", 43), "bosque-rozabales")
    save(mono(forest(*R45, "mist", 45, rays=False)), "bosque-carballeira")

    save(night(*R32, 51), "noche-courel")
    save(night(*R23, 53, horizon=0.86), "noche-ancares")
    save(night(*R169, 55, milky=False, horizon=0.82, meteors=6), "noche-perseidas")

    # ---- Serie destacada y "sobre mí" ----
    save(seascape(2000, 1125, "dusk", (0.52, 0.36), 61), "serie-costa-da-morte", thumb=False)
    save(mono(window_light(1200, 1500, 71)), "estudio", thumb=False)
