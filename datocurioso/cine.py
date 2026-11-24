"""Estilo "cine": una imagen 3D generada por IA para cada escena, con movimiento de cámara,
transiciones con zoom, carteles brillantes y la palabra que se dice en grande en el centro.

Las imágenes se piden gratis a Pollinations (sin clave). Si una falla, esa escena usa la
animación clásica de emojis, así que el video sale siempre.
"""
import math
import os
import time
import urllib.parse
import urllib.request

import cairo

from . import dibujo as D
from .dibujo import W, H, back, ease, col, text, emoji
from .voz import trozos, norm

ESTILO = ("3D animated movie still, Pixar style, cute stylized characters, vibrant saturated colors, "
          "cinematic lighting, depth of field, highly detailed, vertical composition, no text, no letters, no watermark")


def _url(prompt, seed):
    q = urllib.parse.quote(f"{prompt}, {ESTILO}")
    return f"https://image.pollinations.ai/prompt/{q}?width=1080&height=1920&nologo=true&model=flux&seed={seed}"


def descargar_imagenes(historia, carpeta, seed):
    """Baja una imagen por escena (campo `imagen`, prompt en inglés). Devuelve la lista de rutas (None si falla)."""
    os.makedirs(carpeta, exist_ok=True)
    rutas = []
    for i, sc in enumerate(historia["escenas"]):
        prompt = sc.get("imagen")
        if not prompt and sc.get("tipo") != "final":
            prompt = f"{sc['texto']} {sc.get('rotulo') or ''}".strip()  # respaldo si la historia no trae `imagen`
        ruta = os.path.join(carpeta, f"img_{i:02d}.jpg")
        if not prompt:
            rutas.append(None); continue
        if os.path.exists(ruta) and os.path.getsize(ruta) > 20000:
            rutas.append(ruta); continue
        ok = False
        for intento in range(6):
            try:
                req = urllib.request.Request(_url(prompt, seed + i + intento * 101), headers={"User-Agent": "dato-curioso/1.0"})
                with urllib.request.urlopen(req, timeout=180) as r:
                    data = r.read()
                if len(data) > 20000 and (data[:3] == b"\xff\xd8\xff" or data[:8] == b"\x89PNG\r\n\x1a\n"):
                    open(ruta, "wb").write(data); ok = True; break
            except Exception as e:
                print(f"  imagen {i} intento {intento + 1}: {e}")
            time.sleep(30 + intento * 30)  # el servicio gratuito limita la velocidad
        rutas.append(ruta if ok else None)
        time.sleep(16)
    # Si alguna falla, usa la imagen más cercana para no romper el estilo.
    buenas = [k for k, r in enumerate(rutas) if r]
    for k, sc in enumerate(historia["escenas"]):
        if rutas[k] is None and buenas and sc.get("tipo") != "final":
            rutas[k] = rutas[min(buenas, key=lambda b: abs(b - k))]
    return rutas


def _superficie(ruta):
    from PIL import Image
    im = Image.open(ruta).convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((math.ceil(im.width * s), math.ceil(im.height * s)), Image.LANCZOS)
    x = (im.width - W) // 2; y = (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H)).convert("RGBA")
    r, g, b, a = im.split()
    from PIL import Image as I
    data = bytearray(I.merge("RGBA", (b, g, r, a)).tobytes())
    return cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, W, H, W * 4), data


class Cine:
    """Dibuja un fotograma en estilo cine. `clasico` es el Render de emojis para las escenas sin imagen."""

    def __init__(self, historia, meta, rutas, clasico):
        self.h = historia; self.meta = meta; self.clasico = clasico
        self.TOTAL = clasico.TOTAL
        self.words = [w for ch in trozos(meta) for w in ch]
        self.keys = {norm(k) for k in historia.get("claves", [])}
        self.imgs = []
        self._keep = []
        for r in rutas:
            if r:
                s, d = _superficie(r); self.imgs.append(s); self._keep.append(d)
            else:
                self.imgs.append(None)

    def __getattr__(self, k):
        return getattr(self.__dict__["clasico"], k)

    def _escena(self, t):
        li = 0
        for k, m in enumerate(self.meta):
            if t >= m["start"] - 0.12: li = k
        st = self.meta[li]["start"] - 0.12
        en = self.meta[li + 1]["start"] - 0.12 if li + 1 < len(self.meta) else self.TOTAL
        return li, max(0, t - st), en - st

    def _imagen(self, c, li, u, d):
        img = self.imgs[li]
        p = min(1, u / max(d, 0.1))
        # Movimiento de cámara: acercamiento lento + desplazamiento, alternando dirección.
        z = 1.06 + 0.14 * ease(p * 0.9 + 0.1 * p)
        dx = (1 if li % 2 else -1) * 60 * (p - 0.5)
        dy = (-1 if li % 3 else 1) * 40 * (p - 0.5)
        # Entrada con golpe de zoom.
        z += 0.25 * (1 - ease(min(1, u / 0.35)))
        c.save(); c.translate(W / 2 + dx, H / 2 + dy); c.scale(z, z); c.translate(-W / 2, -H / 2)
        c.set_source_surface(img, 0, 0); c.get_source().set_filter(cairo.FILTER_GOOD); c.paint(); c.restore()
        # Viñeta y degradado inferior para que se lean los textos.
        g = cairo.RadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.75)
        g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.55)
        c.set_source(g); c.paint()
        g = cairo.LinearGradient(0, H * 0.55, 0, H)
        g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.6)
        c.set_source(g); c.rectangle(0, H * 0.55, W, H * 0.45); c.fill()

    def _cartel(self, c, sc, u, t):
        """Cartel brillante tipo 'pill' con emoji, como los de los vídeos explicativos."""
        txt = (sc.get("rotulo") or sc.get("sello") or "").upper()
        if sc.get("tipo") == "numero" and sc.get("valor"):
            self._numero(c, sc, u)
        if not txt: return
        p = back((u - 0.25) * 3.5)
        if p <= 0.01: return
        em = (sc.get("emojis") or [None])[0]
        size = 64
        tw = D.text_w(c, txt, size)
        ew = 86 if em else 0
        w = tw + ew + 90; h = 120
        x = W / 2; y = 560 + math.sin(t * 2.2) * 8
        c.save(); c.translate(x, y); c.scale(p, p)
        acento = "#3cff9e" if sc.get("tipo") != "duda" else "#ffb02e"
        if sc.get("tipo") == "sello": acento = "#ff4d4d"
        for k, a in ((34, 0.10), (22, 0.16), (12, 0.24)):
            D.rrect(c, -w / 2 - k, -h / 2 - k, w + 2 * k, h + 2 * k, h / 2 + k); col(c, acento, a); c.fill()
        D.rrect(c, -w / 2, -h / 2, w, h, h / 2); col(c, "#0d1b14", 0.82); c.fill_preserve()
        c.set_line_width(7); col(c, acento); c.stroke()
        x0 = -w / 2 + 45
        if em:
            emoji(c, em, x0 + 38, 0, 84, shadow=False); x0 += ew
        text(c, txt, x0 + tw / 2, 0, size, fill=acento, stroke=None)
        c.restore()

    def _numero(self, c, sc, u):
        val = str(sc["valor"]); p = ease(u / 1.2)
        digs = "".join(ch for ch in val if ch.isdigit())
        if digs:
            n = int(digs); cur = int(n * p)
            s = f"{cur:,}".replace(",", ".") if "." in val or n >= 10000 else str(cur)
            if p >= 1: s = val
        else:
            s = val
        pop = back(u * 3)
        text(c, s, W / 2, 900, 260 * pop, fill="#ffffff", stroke="#000000", sw=0.12, shadow=True)
        if sc.get("unidad"):
            text(c, sc["unidad"].upper(), W / 2, 1060, 70 * pop, fill="#ffd23f", stroke="#000000", sw=0.18)

    def _palabra(self, c, t):
        """La palabra que se está diciendo, enorme, en el centro-abajo (como en los shorts virales)."""
        cur = None
        for w in self.words:
            if w["s"] - 0.03 <= t < w["e"] + 0.02:
                cur = w; break
        if not cur: return
        s = cur["w"].strip(",.;:¿?¡!…\"'«»").lower()
        if not s: return
        u = t - cur["s"]
        pop = 0.85 + 0.15 * back(u * 9)
        fill = "#ffd23f" if norm(cur["w"]) in self.keys else "#ffffff"
        size = 150
        w = D.text_w(c, s, size)
        if w > W - 140: size *= (W - 140) / w
        text(c, s, W / 2, 1390, size * pop, fill=fill, stroke="#000000", sw=0.2, shadow=True)

    def frame(self, t):
        li, u, d = self._escena(t)
        if self.imgs[li] is None or self.h["escenas"][li].get("tipo") == "final":
            return self.clasico.frame(t)
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(surf)
        self._imagen(c, li, u, d)
        if u < 0.14 and li > 0:
            col(c, "#ffffff", 0.5 * (1 - u / 0.14)); c.paint()
        self._cartel(c, self.h["escenas"][li], u, t)
        self._palabra(c, t)
        D.chip(c, "DATO CURIOSO", 540, 170, "#111111", "#ffd23f", 44)
        col(c, "#000000", 0.3); c.rectangle(0, H - 14, W, 14); c.fill()
        col(c, "#ffd23f"); c.rectangle(0, H - 14, W * t / self.TOTAL, 14); c.fill()
        return surf
