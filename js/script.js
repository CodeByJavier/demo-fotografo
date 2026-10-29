/**
 * IRIA SEOANE — FOTOGRAFÍA DE PAISAJE
 * JavaScript en vanilla JS, sin dependencias. Cada módulo "init..." es
 * independiente y se ejecuta aislado con safeRun(): si uno falla, el resto
 * de la página sigue funcionando.
 *
 * Reutilizado de Casa Verdés (sin cambios): utilidades de foco y scroll,
 * cabecera, menú móvil y animaciones de aparición.
 * Nuevo en esta plantilla:
 *  - initSlideshow: pase de fotos de la portada, con pausa y movimiento reducido.
 *  - initFilters:   filtrado del portfolio por serie, anunciado al lector de pantalla.
 *  - initLightbox:  visor que respeta el filtro, con datos de toma y deslizamiento táctil.
 *  - initPrefill:   los botones de copias rellenan el formulario de contacto.
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", init);

  function init() {
    safeRun(setFooterYear);
    safeRun(initHeaderScroll);
    safeRun(initMenu);
    safeRun(initReveal);
    safeRun(initSlideshow);
    safeRun(initFilters);
    safeRun(initLightbox);
    safeRun(initPrefill);
    safeRun(initContactForm);
  }

  function safeRun(fn) {
    try {
      fn();
    } catch (error) {
      console.error("[IriaSeoane] Error en " + fn.name + ":", error);
    }
  }

  /* =====================================================================
   * Utilidades compartidas
   * =================================================================== */

  var FOCUSABLE = [
    "a[href]",
    "button:not([disabled])",
    "input:not([disabled])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    '[tabindex]:not([tabindex="-1"])',
  ].join(",");

  /**
   * Mantiene el foco dentro de un contenedor mientras está abierto.
   * Es lo que convierte una capa "que tapa la pantalla" en un diálogo de
   * verdad: sin esto, con el tabulador te vas a los enlaces de detrás y el
   * lector de pantalla se pierde fuera de la ventana modal.
   * Devuelve una función para desactivarlo.
   */
  /**
   * Mueve el foco a un elemento de una capa que se acaba de abrir.
   * focus() sobre un elemento con visibility:hidden no hace nada y no da
   * error. Por eso el CSS cambia visibility al instante al abrir (sin
   * transición) y aquí se fuerza el cálculo de estilos antes de enfocar.
   * Si aun así no lo consigue, lo reintenta en el siguiente fotograma.
   */
  function focusWhenVisible(el) {
    if (!el) return;
    void el.offsetHeight;
    el.focus();
    if (document.activeElement !== el) {
      window.requestAnimationFrame(function () {
        el.focus();
      });
    }
  }

  function trapFocus(container) {
    function onKeydown(event) {
      if (event.key !== "Tab") return;

      var items = Array.prototype.filter.call(
        container.querySelectorAll(FOCUSABLE),
        function (el) {
          return el.offsetParent !== null || el === document.activeElement;
        }
      );
      if (!items.length) return;

      var first = items[0];
      var last = items[items.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeydown);
    return function release() {
      document.removeEventListener("keydown", onKeydown);
    };
  }

  /** Bloquea el scroll del fondo compensando el ancho de la barra para que no "salte". */
  function lockScroll(locked) {
    if (locked) {
      var gap = window.innerWidth - document.documentElement.clientWidth;
      document.body.style.overflow = "hidden";
      if (gap > 0) document.body.style.paddingRight = gap + "px";
    } else {
      document.body.style.overflow = "";
      document.body.style.paddingRight = "";
    }
  }

  /* =====================================================================
   * Año del pie
   * =================================================================== */
  function setFooterYear() {
    var year = new Date().getFullYear();
    document.querySelectorAll("[data-year]").forEach(function (el) {
      el.textContent = year;
    });
  }

  /* =====================================================================
   * Cabecera: pasa a sólida al bajar
   * =================================================================== */
  function initHeaderScroll() {
    var header = document.getElementById("header");
    if (!header) return;

    function onScroll() {
      header.classList.toggle("is-scrolled", window.scrollY > 40);
    }
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* =====================================================================
   * Menú móvil: panel lateral
   * En escritorio la navegación es una barra visible y este módulo no
   * interviene; solo actúa cuando el CSS ha convertido la <nav> en panel.
   * =================================================================== */
  function initMenu() {
    var btn = document.getElementById("menuBtn");
    var nav = document.getElementById("menu");
    var header = document.getElementById("header");
    var backdrop = document.getElementById("navBackdrop");
    if (!btn || !nav || !header || !backdrop) return;

    var label = btn.querySelector("[data-menu-label]");
    // Debe coincidir con la media query del CSS (max-width: 959px)
    var mobile = window.matchMedia("(max-width: 959px)");
    var releaseTrap = null;

    function isOpen() {
      return nav.classList.contains("is-open");
    }

    function open() {
      nav.classList.add("is-open");
      backdrop.hidden = false;
      void backdrop.offsetHeight; // estado inicial para que se vea el fundido
      backdrop.classList.add("is-visible");
      btn.setAttribute("aria-expanded", "true");
      if (label) label.textContent = "Cerrar";
      lockScroll(true);
      // La trampa abarca toda la cabecera: así el botón de cerrar, que está
      // fuera de la <nav>, sigue siendo alcanzable con el tabulador.
      releaseTrap = trapFocus(header);
      focusWhenVisible(nav.querySelector("a[href]"));
    }

    function close(returnFocus) {
      if (!isOpen()) return;
      nav.classList.remove("is-open");
      backdrop.classList.remove("is-visible");
      btn.setAttribute("aria-expanded", "false");
      if (label) label.textContent = "Menú";
      lockScroll(false);
      if (releaseTrap) {
        releaseTrap();
        releaseTrap = null;
      }
      if (returnFocus !== false) btn.focus();

      window.setTimeout(function () {
        if (!isOpen()) backdrop.hidden = true;
      }, 400);
    }

    btn.addEventListener("click", function () {
      if (isOpen()) close();
      else open();
    });

    backdrop.addEventListener("click", function () {
      close();
    });

    nav.querySelectorAll("a[href^='#']").forEach(function (link) {
      link.addEventListener("click", function () {
        close(false);
      });
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") close();
    });

    // Si se agranda la ventana con el panel abierto (girar una tablet,
    // por ejemplo), se cierra para no dejar el scroll bloqueado.
    function onBreakpointChange(event) {
      if (!event.matches) close(false);
    }
    if (mobile.addEventListener) mobile.addEventListener("change", onBreakpointChange);
    else if (mobile.addListener) mobile.addListener(onBreakpointChange);
  }

  /* =====================================================================
   * Aparición al hacer scroll
   * =================================================================== */
  function initReveal() {
    var items = document.querySelectorAll("[data-reveal]");
    if (!items.length) return;

    items.forEach(function (item) {
      var delay = item.getAttribute("data-reveal-delay");
      if (delay) item.style.setProperty("--reveal-delay", delay + "ms");
    });

    if (!("IntersectionObserver" in window)) {
      items.forEach(function (item) {
        item.classList.add("is-visible");
      });
      return;
    }

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );

    items.forEach(function (item) {
      observer.observe(item);
    });
  }

  /* =====================================================================
   * Pase de fotos de la portada
   * La barra de progreso de cada punto es una animación CSS y es ELLA la que
   * marca el cambio de foto (evento animationend). Así pausar es simplemente
   * congelar la animación (animation-play-state: paused) y el tiempo que
   * faltaba se respeta solo, sin cuentas con setTimeout.
   * =================================================================== */
  function initSlideshow() {
    var root = document.querySelector("[data-slideshow]");
    if (!root) return;

    var slides = Array.prototype.slice.call(root.querySelectorAll(".hero__slide"));
    var dots = Array.prototype.slice.call(root.querySelectorAll(".hero__dot"));
    var toggle = root.querySelector("[data-slide-toggle]");
    var caption = root.querySelector("[data-slide-caption]");
    var captionTitle = root.querySelector("[data-caption-title]");
    var captionMeta = root.querySelector("[data-caption-meta]");
    var counter = root.querySelector("[data-slide-counter]");
    if (slides.length < 2 || dots.length !== slides.length) return;

    var SLIDE_MS = 6500;
    root.style.setProperty("--slide-ms", SLIDE_MS + "ms");

    var current = 0;
    var userPaused = false;
    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function pad(n) {
      return n < 10 ? "0" + n : String(n);
    }

    function show(index) {
      current = (index + slides.length) % slides.length;

      slides.forEach(function (slide, i) {
        var active = i === current;
        slide.classList.toggle("is-active", active);
        slide.setAttribute("aria-hidden", active ? "false" : "true");
      });

      dots.forEach(function (dot, i) {
        dot.classList.toggle("is-done", i < current);
        dot.classList.remove("is-active");
        if (i === current) dot.setAttribute("aria-current", "true");
        else dot.removeAttribute("aria-current");
      });
      // Reiniciar la animación de la barra: quitar la clase, forzar un
      // reflujo y volver a ponerla. Sin el reflujo, el navegador junta los
      // dos cambios en uno y la animación no vuelve a empezar.
      void dots[current].offsetWidth;
      dots[current].classList.add("is-active");

      var slide = slides[current];
      if (captionTitle) captionTitle.textContent = slide.getAttribute("data-title");
      if (captionMeta) {
        captionMeta.textContent = slide.getAttribute("data-place") + " — " + slide.getAttribute("data-exif");
      }
      if (counter) counter.textContent = pad(current + 1) + " / " + pad(slides.length);
    }

    function setPaused(paused) {
      root.classList.toggle("is-paused", paused);
      if (toggle) {
        toggle.setAttribute("aria-label", paused ? "Reanudar el pase de fotos" : "Pausar el pase de fotos");
        var use = toggle.querySelector("use");
        if (use) use.setAttribute("href", paused ? "#i-play" : "#i-pause");
      }
      // En pausa los cambios los provoca el usuario: entonces sí se anuncian
      if (caption) caption.setAttribute("aria-live", paused ? "polite" : "off");
    }

    dots.forEach(function (dot, i) {
      // Al terminar de rellenarse la barra activa, se pasa a la siguiente foto
      dot.querySelector(".hero__dot-fill").addEventListener("animationend", function () {
        if (i === current && !root.classList.contains("is-paused")) show(current + 1);
      });
      dot.addEventListener("click", function () {
        show(i);
      });
    });

    if (toggle) {
      toggle.addEventListener("click", function () {
        userPaused = !root.classList.contains("is-paused");
        setPaused(userPaused);
      });
    }

    // Con la pestaña oculta no tiene sentido seguir pasando fotos
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) setPaused(true);
      else if (!userPaused) setPaused(false);
    });

    // Con "reducir movimiento" activado en el sistema, arranca en pausa
    if (reduceMotion) userPaused = true;
    setPaused(userPaused);
    show(0);
  }

  /* =====================================================================
   * Filtros del portfolio
   * =================================================================== */
  function initFilters() {
    var buttons = Array.prototype.slice.call(document.querySelectorAll("[data-filter]"));
    var shots = Array.prototype.slice.call(document.querySelectorAll("[data-gallery] .shot"));
    var status = document.querySelector("[data-gallery-status]");
    if (!buttons.length || !shots.length) return;

    function apply(filter) {
      var visible = 0;
      shots.forEach(function (shot) {
        var match = filter === "todas" || shot.getAttribute("data-series") === filter;
        shot.hidden = !match;
        if (match) {
          visible++;
          // Una foto que estaba oculta no ha pasado por el observador de
          // aparición: se marca visible para que no se quede transparente
          shot.classList.add("is-visible");
        }
      });

      buttons.forEach(function (btn) {
        btn.setAttribute("aria-pressed", String(btn.getAttribute("data-filter") === filter));
      });

      if (status) {
        var active = buttons.filter(function (b) { return b.getAttribute("aria-pressed") === "true"; })[0];
        var name = active ? active.firstChild.textContent.trim() : "";
        status.textContent = "Mostrando " + visible + (visible === 1 ? " foto" : " fotos") +
          (filter === "todas" ? "" : " de la serie " + name);
      }
    }

    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        apply(btn.getAttribute("data-filter"));
      });
    });

    // Enlaces desde otras secciones que llevan al portfolio ya filtrado
    document.querySelectorAll("[data-filter-link]").forEach(function (link) {
      link.addEventListener("click", function () {
        apply(link.getAttribute("data-filter-link"));
      });
    });
  }

  /* =====================================================================
   * Visor a pantalla completa
   * Recorre solo las fotos VISIBLES (respeta el filtro activo), muestra la
   * versión grande, los datos de toma, y en móvil se pasa de foto deslizando.
   * =================================================================== */
  function initLightbox() {
    var gallery = document.querySelector("[data-gallery]");
    var box = document.getElementById("lightbox");
    if (!gallery || !box) return;

    var img = box.querySelector("[data-lightbox-img]");
    var stage = box.querySelector("[data-lightbox-stage]");
    var title = box.querySelector("[data-lightbox-title]");
    var place = box.querySelector("[data-lightbox-place]");
    var exif = box.querySelector("[data-lightbox-exif]");
    var counter = box.querySelector("[data-lightbox-counter]");
    var btnPrev = box.querySelector("[data-lightbox-prev]");
    var btnNext = box.querySelector("[data-lightbox-next]");
    var btnClose = box.querySelector("[data-lightbox-close]");

    var items = [];
    var index = 0;
    var lastFocused = null;
    var releaseTrap = null;

    function visibleItems() {
      return Array.prototype.filter.call(gallery.querySelectorAll(".shot__open"), function (btn) {
        return !btn.closest(".shot").hidden;
      });
    }

    function preload(i) {
      var item = items[(i + items.length) % items.length];
      if (item) new Image().src = item.getAttribute("data-full");
    }

    function render() {
      var item = items[index];
      var thumb = item.querySelector("img");

      img.classList.add("is-loading");
      img.onload = function () {
        img.classList.remove("is-loading");
      };
      img.setAttribute("src", item.getAttribute("data-full"));
      img.setAttribute("alt", thumb ? thumb.getAttribute("alt") : "");
      if (img.complete) img.classList.remove("is-loading");

      title.textContent = item.getAttribute("data-title");
      place.textContent = item.getAttribute("data-place");
      exif.textContent = item.getAttribute("data-exif");
      counter.textContent = index + 1 + " / " + items.length;

      // Adelanta la descarga de las vecinas para que el paso sea inmediato
      preload(index + 1);
      preload(index - 1);
    }

    function open(trigger) {
      items = visibleItems();
      index = Math.max(0, items.indexOf(trigger));
      lastFocused = trigger;
      render();
      box.hidden = false;
      void box.offsetHeight;
      box.classList.add("is-open");
      lockScroll(true);
      releaseTrap = trapFocus(box);
      focusWhenVisible(btnClose);
    }

    function close() {
      if (!box.classList.contains("is-open")) return;
      box.classList.remove("is-open");
      lockScroll(false);
      if (releaseTrap) {
        releaseTrap();
        releaseTrap = null;
      }
      if (lastFocused) lastFocused.focus();
      window.setTimeout(function () {
        if (!box.classList.contains("is-open")) box.hidden = true;
      }, 350);
    }

    function go(step) {
      if (items.length < 2) return;
      index = (index + step + items.length) % items.length;
      render();
    }

    gallery.addEventListener("click", function (event) {
      var trigger = event.target.closest(".shot__open");
      if (trigger) open(trigger);
    });

    btnPrev.addEventListener("click", function () { go(-1); });
    btnNext.addEventListener("click", function () { go(1); });
    btnClose.addEventListener("click", close);

    // Pulsar el fondo (fuera de la foto) cierra
    stage.addEventListener("click", function (event) {
      if (event.target === stage) close();
    });

    document.addEventListener("keydown", function (event) {
      if (!box.classList.contains("is-open")) return;
      if (event.key === "Escape") close();
      else if (event.key === "ArrowLeft") go(-1);
      else if (event.key === "ArrowRight") go(1);
    });

    // Deslizar en pantallas táctiles: más de 50 px en horizontal y más
    // horizontal que vertical cuenta como "pasar de foto"
    var startX = null;
    var startY = null;
    stage.addEventListener("pointerdown", function (event) {
      if (event.pointerType === "mouse") return;
      startX = event.clientX;
      startY = event.clientY;
    });
    stage.addEventListener("pointerup", function (event) {
      if (startX === null) return;
      var dx = event.clientX - startX;
      var dy = event.clientY - startY;
      startX = startY = null;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) go(dx < 0 ? 1 : -1);
    });
    stage.addEventListener("pointercancel", function () {
      startX = startY = null;
    });
  }

  /* =====================================================================
   * Botones "Pedir esta copia": rellenan el formulario y llevan a él
   * (mismo patrón que el presupuesto exprés de la plantilla del taller)
   * =================================================================== */
  function initPrefill() {
    var form = document.getElementById("contactForm");
    if (!form) return;

    document.querySelectorAll("[data-prefill]").forEach(function (link) {
      link.addEventListener("click", function () {
        var reason = form.elements.reason;
        var message = form.elements.message;
        if (reason) {
          reason.value = link.getAttribute("data-prefill");
          reason.dispatchEvent(new Event("change"));
        }
        if (message && !message.value.trim()) {
          message.value = link.getAttribute("data-prefill-text") || "";
        }
        // El enlace ya hace scroll hasta #contacto; el foco va al primer
        // campo para poder escribir directamente
        window.setTimeout(function () {
          if (form.elements.name) form.elements.name.focus({ preventScroll: true });
        }, 500);
      });
    });
  }

  /* =====================================================================
   * Formulario de contacto
   * =================================================================== */
  function initContactForm() {
    var form = document.getElementById("contactForm");
    if (!form) return;

    var submitBtn = document.getElementById("submitBtn");
    var submitLabel = form.querySelector("[data-submit-label]");
    var spinner = form.querySelector("[data-spinner]");
    var statusBox = form.querySelector("[data-form-status]");

    var validators = {
      name: function (value) {
        return value.trim().length >= 2 ? "" : "Escribe tu nombre.";
      },
      email: function (value) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim()) ? "" : "Escribe un correo electrónico válido.";
      },
      reason: function (value) {
        return value ? "" : "Elige el motivo de tu mensaje.";
      },
      message: function (value) {
        return value.trim().length >= 10 ? "" : "Cuéntame un poco más (mínimo 10 caracteres).";
      },
      privacy: function (_value, input) {
        return input.checked ? "" : "Debes aceptar la política de privacidad.";
      },
    };

    function validateField(input) {
      var validator = validators[input.name];
      if (!validator) return true;
      var message = validator(input.value, input);
      var wrapper = input.closest(".field");
      var errorEl = form.querySelector('[data-error-for="' + input.name + '"]');
      if (wrapper) wrapper.classList.toggle("has-error", Boolean(message));
      if (errorEl) errorEl.textContent = message;
      return !message;
    }

    var tracked = Array.prototype.filter.call(form.elements, function (el) {
      return el.name && validators[el.name];
    });

    tracked.forEach(function (input) {
      var evt = input.tagName === "SELECT" || input.type === "checkbox" ? "change" : "blur";
      input.addEventListener(evt, function () {
        validateField(input);
      });
      input.addEventListener("input", function () {
        var wrapper = input.closest(".field");
        if (wrapper && wrapper.classList.contains("has-error")) validateField(input);
      });
    });

    function showStatus(state, text) {
      if (!statusBox) return;
      statusBox.hidden = false;
      statusBox.setAttribute("data-state", state);
      statusBox.textContent = text;
    }

    function setLoading(loading) {
      if (submitBtn) submitBtn.disabled = loading;
      if (spinner) spinner.hidden = !loading;
      if (submitLabel) submitLabel.textContent = loading ? "Enviando..." : "Enviar mensaje";
    }

    /**
     * Envío simulado. Sustituir por una llamada real, por ejemplo a un
     * servicio de formularios (Formspree, Netlify Forms...) o a un backend:
     *   fetch('https://formspree.io/f/TU_ID', { method: 'POST', body: new FormData(form) })
     * En la demo falla un 12% de las veces para poder ver el estado de error.
     */
    function send(payload) {
      return new Promise(function (resolve, reject) {
        window.setTimeout(function () {
          if (Math.random() < 0.88) resolve({ ok: true, payload: payload });
          else reject(new Error("No se ha podido enviar el mensaje. Inténtalo de nuevo en unos segundos."));
        }, 1100);
      });
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      if (statusBox) statusBox.hidden = true;

      var valid = tracked.map(validateField).every(Boolean);
      if (!valid) {
        showStatus("error", "Revisa los campos marcados antes de enviar.");
        var firstInvalid = form.querySelector(".has-error input, .has-error select, .has-error textarea");
        if (firstInvalid) firstInvalid.focus();
        return;
      }

      var payload = {};
      new FormData(form).forEach(function (value, key) {
        payload[key] = value;
      });

      setLoading(true);
      send(payload)
        .then(function () {
          showStatus("success", "¡Gracias! Te respondo en menos de 48 horas.");
          form.reset();
          tracked.forEach(function (input) {
            var wrapper = input.closest(".field");
            if (wrapper) wrapper.classList.remove("has-error");
          });
        })
        .catch(function (error) {
          showStatus("error", error.message || "Ha ocurrido un error inesperado.");
        })
        .finally(function () {
          setLoading(false);
        });
    });
  }
})();
