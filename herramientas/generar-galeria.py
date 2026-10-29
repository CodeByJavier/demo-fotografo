#!/usr/bin/env python3
"""
Genera el bloque HTML de la galería y los botones de filtro a partir de la
lista de fotos, leyendo el tamaño REAL de cada imagen.

Por qué existe: en srcset el descriptor "w" es el ancho real del archivo.
Una miniatura vertical mide 533 px de ancho, no 800; si se declara mal, el
navegador elige la imagen equivocada. Escribirlo a mano en 14 fotos es la
forma más fácil de equivocarse, así que lo calcula este script.

Uso:  python herramientas/generar-galeria.py
Reescribe las zonas marcadas con <!--GALERIA--> y <!--FILTROS--> en index.html
(o lo que haya entre los comentarios de inicio y fin si ya se generó antes).
"""
import os
import re
from html import escape
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "img")
INDEX = os.path.join(ROOT, "index.html")

SERIES = {"costa": "Costa", "montana": "Montaña", "bosque": "Bosque", "noche": "Noche"}

# Orden intercalado para que "Todas" mezcle series y no se vean bloques
FOTOS = [
    ("costa-fisterra", "Último sol en Fisterra", "Fisterra, A Coruña", "f/11 · 1/250 s · ISO 100 · 70 mm",
     "Atardecer anaranjado sobre el mar con un islote a contraluz en el horizonte"),
    ("montana-ancares", "Os Ancares en enero", "Os Ancares, Lugo", "f/9 · 1/200 s · ISO 200 · 105 mm",
     "Capas de montañas en blanco y negro difuminadas por la niebla"),
    ("bosque-eume", "Fragas do Eume", "Pontedeume, A Coruña", "f/5.6 · 1/60 s · ISO 400 · 35 mm",
     "Troncos altos de un bosque atravesado por haces de luz entre la niebla"),
    ("noche-courel", "Vía Láctea sobre O Courel", "Serra do Courel, Lugo", "f/2.8 · 20 s · ISO 3200 · 14 mm",
     "La Vía Láctea cruzando el cielo estrellado sobre la silueta de las montañas"),
    ("costa-cies", "Amanecer frente a las Cíes", "Monteferro, Nigrán", "f/8 · 1/320 s · ISO 100 · 35 mm",
     "Mar en calma al amanecer con el cielo dorado sobre el horizonte"),
    ("montana-ribeira", "Inversión térmica", "Ribeira Sacra, Ourense", "f/8 · 1/160 s · ISO 100 · 85 mm",
     "Crestas de montaña asomando sobre un mar de niebla al amanecer"),
    ("noche-perseidas", "Perseidas", "Costa da Morte", "f/2.8 · 15 s · ISO 3200 · 20 mm",
     "Varias estrellas fugaces cruzando un cielo nocturno sobre las montañas"),
    ("costa-trece", "Praia do Trece", "Camariñas, A Coruña", "f/16 · 30 s · ISO 50 · 24 mm",
     "Fotografía en blanco y negro de dos farallones a contraluz frente a un mar liso de larga exposición"),
    ("bosque-rozabales", "Souto de Rozabales", "Manzaneda, Ourense", "f/8 · 1/30 s · ISO 200 · 24 mm",
     "Bosque de troncos finos envuelto en niebla"),
    ("montana-capelada", "Serra da Capelada", "Cariño, A Coruña", "f/10 · 1/200 s · ISO 100 · 135 mm",
     "Montañas superpuestas en tonos cálidos bajo un cielo de atardecer"),
    ("costa-vilan", "Hora azul en Cabo Vilán", "Camariñas, A Coruña", "f/8 · 4 s · ISO 100 · 50 mm",
     "Mar azulado en la hora azul con un pequeño islote en el horizonte"),
    ("noche-ancares", "Cielo de agosto", "Os Ancares, Lugo", "f/2.8 · 25 s · ISO 4000 · 14 mm",
     "Franja de la Vía Láctea en vertical sobre una cresta montañosa"),
    ("montana-courel", "Valles del Courel", "Serra do Courel, Lugo", "f/11 · 1/125 s · ISO 100 · 50 mm",
     "Laderas suaves en tonos verdes que se pierden en la bruma"),
    ("bosque-carballeira", "Carballeira na néboa", "Santiago de Compostela", "f/8 · 1/50 s · ISO 400 · 50 mm",
     "Fotografía en blanco y negro de troncos de roble recortados contra la niebla"),
]

# Ancho de la columna en cada tamaño de pantalla (coincide con style.css:
# 1 columna < 560 px, 2 columnas hasta 1099 px, 3 a partir de ahí)
SIZES = "(min-width: 1320px) 410px, (min-width: 1100px) 31vw, (min-width: 560px) 46vw, 92vw"


def size(name):
    with Image.open(os.path.join(IMG, name)) as im:
        return im.size


def figure(slug, title, place, exif, alt):
    serie = slug.split("-")[0]
    fw, fh = size(f"{slug}.jpg")
    tw, th = size(f"{slug}-800.jpg")
    a = escape(alt, quote=True)
    return f'''          <figure class="shot" data-series="{serie}" data-reveal>
            <button type="button" class="shot__open" aria-label="Ampliar «{escape(title)}»"
                    data-full="img/{slug}.jpg" data-title="{escape(title, quote=True)}" data-place="{escape(place, quote=True)}" data-exif="{escape(exif, quote=True)}">
              <img src="img/{slug}-800.jpg" srcset="img/{slug}-800.jpg {tw}w, img/{slug}.jpg {fw}w" sizes="{SIZES}"
                   alt="{a}" width="{tw}" height="{th}" loading="lazy" decoding="async" />
              <span class="shot__exif mono" aria-hidden="true">{escape(exif)}</span>
            </button>
            <figcaption><span class="shot__title">{escape(title)}</span><span class="shot__place">{escape(place)}</span></figcaption>
          </figure>'''


def filters():
    counts = {k: sum(1 for f in FOTOS if f[0].startswith(k + "-")) for k in SERIES}
    items = [f'            <li><button type="button" data-filter="todas" aria-pressed="true">Todas<sup>{len(FOTOS)}</sup></button></li>']
    for key, label in SERIES.items():
        items.append(f'            <li><button type="button" data-filter="{key}" aria-pressed="false">{label}<sup>{counts[key]}</sup></button></li>')
    return "\n".join(items)


def inject(html, marker, content):
    start, end = f"<!--{marker}:inicio-->", f"<!--{marker}:fin-->"
    block = f"{start}\n{content}\n{end}"
    if start in html:
        return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: block, html, flags=re.S)
    return html.replace(f"<!--{marker}-->", block)


if __name__ == "__main__":
    html = open(INDEX, encoding="utf-8").read()
    html = inject(html, "GALERIA", "\n".join(figure(*f) for f in FOTOS))
    html = inject(html, "FILTROS", filters())
    open(INDEX, "w", encoding="utf-8").write(html)
    print(f"Galería generada: {len(FOTOS)} fotos")
