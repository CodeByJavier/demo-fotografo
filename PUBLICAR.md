# Publicar en GitHub Pages

**Cómo funciona, con una analogía:** el repositorio de GitHub es el almacén
donde guardas los archivos, y GitHub Pages es un escaparate gratuito que
GitHub monta delante de ese almacén. Cada vez que subes algo nuevo
(`git push`), el escaparate se actualiza solo en uno o dos minutos.

La dirección final será:

```
https://codebyjavier.github.io/demo-fotografo/
```

El nombre de la carpeta en tu ordenador da igual. La dirección la decide el
**nombre del repositorio**: por eso conviene que sea corto, en minúsculas y
sin espacios.

---

## 1. Crear el repositorio en GitHub

1. Entra en <https://github.com/new>.
2. **Repository name:** `demo-fotografo`
3. Márcalo como **Public**. En una cuenta gratuita, Pages solo publica
   repositorios públicos.
4. **No marques** «Add a README», «.gitignore» ni «license». El repositorio
   tiene que nacer vacío: si GitHub crea un archivo por su cuenta, tu primer
   `push` choca con ese historial (ver «Problemas frecuentes»).
5. Pulsa **Create repository**.

## 2. Subir los archivos

Abre una terminal **en la carpeta del proyecto** (en VS Code: *Terminal →
New Terminal*, ya se abre en la carpeta abierta) y ejecuta, línea a línea:

```bash
git init
git add .
git status
git commit -m "Primera versión de la web de fotógrafo"
git branch -M main
git remote add origin https://github.com/CodeByJavier/demo-fotografo.git
git push -u origin main
```

Qué hace cada una:

| Comando | Qué hace |
|---|---|
| `git init` | Convierte la carpeta en un repositorio (crea la carpeta oculta `.git`). |
| `git add .` | Prepara todos los archivos para el siguiente commit. |
| `git status` | **Revisa antes de seguir**: la lista en verde es lo que se va a subir. Si sale algo que no debería (una copia de seguridad, archivos personales), quítalo antes de hacer commit. |
| `git commit -m "…"` | Guarda una «foto» del proyecto con ese mensaje. |
| `git branch -M main` | Llama `main` a la rama principal, que es el nombre que espera GitHub. |
| `git remote add origin …` | Le dice a tu repositorio local dónde está su copia en GitHub. |
| `git push -u origin main` | Sube la rama. El `-u` hace que los próximos `push` no necesiten repetir `origin main`. |

Si al hacer `push` te pide iniciar sesión, en Windows se abrirá una ventana
del navegador. Ojo: GitHub **no acepta la contraseña de la cuenta** en la
terminal; usa esa ventana o un token personal.

## 3. Activar GitHub Pages

1. En el repositorio, ve a **Settings → Pages**.
2. En **Build and deployment → Source**, elige **Deploy from a branch**.
3. En **Branch**, elige `main` y la carpeta `/ (root)`. Pulsa **Save**.
4. Espera uno o dos minutos. Puedes ver el progreso en la pestaña
   **Actions**. Cuando termine, la dirección aparece arriba en la misma
   página de *Settings → Pages*.

## 4. Después de publicar

En `index.html`, la etiqueta `og:image` (la imagen que aparece al compartir el
enlace por WhatsApp o redes sociales) tiene que ser una dirección completa
para que funcione. Cámbiala por:

```html
<meta property="og:image" content="https://codebyjavier.github.io/demo-fotografo/img/portada-1.jpg" />
```

y súbelo:

```bash
git add index.html
git commit -m "Imagen para compartir con URL absoluta"
git push
```

## 5. Actualizar la web más adelante

Cada cambio se publica con los mismos tres pasos:

```bash
git add .
git commit -m "Describe aquí el cambio"
git push
```

---

## Problemas frecuentes

**La dirección da error 404.**
Espera un par de minutos tras activar Pages. Si sigue igual, abre el
repositorio en GitHub y comprueba que `index.html` aparece **en la raíz** y no
dentro de una subcarpeta. Esto pasa si se hace `git init` en la carpeta de
arriba (por ejemplo, en `Programacion Web`) en vez de en la del proyecto.

**En tu ordenador se ven las imágenes pero en GitHub Pages no.**
Casi siempre son mayúsculas: Windows considera iguales `Foto.jpg` y `foto.jpg`
y GitHub Pages no. En este proyecto todos los nombres están en minúsculas y
ya se ha comprobado que cada ruta coincide exactamente con su archivo; si
añades fotos nuevas, mantén la misma regla.

**`git push` falla con «rejected… fetch first».**
El repositorio de GitHub no estaba vacío (se creó con un README). Trae ese
historial y vuelve a subir:

```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

**Has cambiado algo pero la web sigue igual.**
Espera un minuto (mira la pestaña *Actions*) y recarga sin caché con
`Ctrl + F5`.

**El formulario no envía nada.**
Es normal: está simulado, porque GitHub Pages solo sirve archivos y no puede
procesar formularios. El README explica cómo conectarlo a Formspree.
