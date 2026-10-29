# Iria Seoane · Fotografía de paisaje

Plantilla de web para fotógrafos de paisaje y viaje: portfolio por series,
serie destacada, venta de copias de autor, «sobre mí» y contacto.

Es una demo: el nombre, los textos y las fotos son de ejemplo.

## Qué incluye

- **Portada con pase de fotos.** Se puede pausar, arranca en pausa si el
  sistema tiene activado «reducir movimiento» y muestra los datos de toma de
  cada foto.
- **Portfolio filtrable por series** en mosaico de columnas que respeta la
  proporción original de cada foto (no recorta ninguna).
- **Visor a pantalla completa.** Funciona con teclado, recorre solo las fotos
  del filtro activo y en móvil se pasa de foto deslizando el dedo.
- **Copias de autor** presentadas como láminas enmarcadas (hechas solo con
  CSS). El botón de cada copia rellena el formulario de contacto.
- **Imágenes adaptativas** (`srcset`): el móvil descarga versiones más ligeras.
- Accesibilidad comprobada: contraste AA, orden de encabezados, foco atrapado
  en el menú y el visor, anuncios para lector de pantalla.

HTML, CSS y JavaScript sin librerías ni frameworks.

## Estructura

```
index.html
css/style.css
js/script.js
img/                         fotos (cada una en 1600 px y en 800 px: «-800»)
herramientas/
  generar-imagenes.py        crea las fotos de ejemplo
  generar-galeria.py         escribe el HTML de la galería a partir de la lista de fotos
```

## Poner las fotos reales del cliente

**Opción rápida:** sustituir cada archivo de `img/` por otro **con el mismo
nombre**. Para cada foto de la galería hacen falta dos versiones: la grande
(lado largo de 1600 px) y la miniatura con `-800` (lado largo de 800 px).

**Opción completa** (si cambian las fotos, sus títulos o su número):

1. Copia las fotos en `img/`, en sus dos tamaños.
2. Edita la lista `FOTOS` de `herramientas/generar-galeria.py` (archivo,
   título, lugar, datos de toma y texto alternativo).
3. Ejecuta `python herramientas/generar-galeria.py`. El script mide cada foto
   y escribe en `index.html` el ancho y el alto correctos y los `srcset`.
   Escribir eso a mano es la forma más fácil de equivocarse.

El script necesita Pillow: `pip install pillow`.

## Formulario de contacto

El envío está **simulado** (ver `send()` en `js/script.js`). GitHub Pages solo
sirve archivos estáticos y no puede recibir formularios. Para que lleguen los
mensajes de verdad, la forma más sencilla es un servicio como
[Formspree](https://formspree.io): se crea un formulario gratuito y se cambia
la simulación por:

```js
fetch("https://formspree.io/f/TU_ID", { method: "POST", body: new FormData(form), headers: { Accept: "application/json" } })
```

## Publicar en GitHub Pages

Las instrucciones están en [PUBLICAR.md](PUBLICAR.md).
