"""Dato Curioso: generación y publicación automática de shorts.

  python -m datocurioso comprobar        revisa que todo esté instalado
  python -m datocurioso autorizar        conecta tu canal de YouTube (una sola vez)
  python -m datocurioso previa [ID]      genera una imagen con todas las escenas (rápido)
  python -m datocurioso render [ID]      genera el video sin subirlo
  python -m datocurioso lote             rellena los huecos de publicación de las próximas horas (lo que ejecuta la tarea programada)
  python -m datocurioso estado           muestra lo programado y lo que queda en cola
"""
import argparse
import datetime as dt
import json
import os
import sys
import traceback

from . import config, historias, metadatos

try:
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _tz(cfg):
    from zoneinfo import ZoneInfo
    return ZoneInfo(cfg["zona_horaria"])


def _reg_path(cfg):
    return os.path.join(cfg["carpeta_salida"], "registro.json")


def leer_registro(cfg):
    p = _reg_path(cfg)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f: return json.load(f)
    return {"videos": {}}


def guardar_registro(cfg, reg):
    p = _reg_path(cfg); tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(reg, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def log(cfg, msg):
    linea = f"[{dt.datetime.now():%Y-%m-%d %H:%M}] {msg}"
    print(linea)
    with open(os.path.join(cfg["carpeta_salida"], "registro.log"), "a", encoding="utf-8") as f: f.write(linea + "\n")


def huecos(cfg, reg, ahora):
    tz = _tz(cfg); ahora = ahora.astimezone(tz)
    ocupados = {v.get("publicar_en") or v.get("reservado") for v in reg["videos"].values()} - {None}
    ini = ahora + dt.timedelta(minutes=cfg["margen_minutos"]); fin = ahora + dt.timedelta(hours=cfg["horizonte_horas"])
    out = []
    for dia in range(0, 3):
        fecha = (ahora + dt.timedelta(days=dia)).date()
        for hh in cfg["horas_publicacion"]:
            h, m = map(int, hh.split(":"))
            s = dt.datetime(fecha.year, fecha.month, fecha.day, h, m, tzinfo=tz)
            if ini <= s <= fin and s.isoformat() not in ocupados: out.append(s)
    return sorted(set(out))


def buscar(cfg, ident):
    reg = leer_registro(cfg)
    if ident:
        for r, h in historias.todas():
            if h["id"] == ident or os.path.basename(r).startswith(ident): return h
        raise SystemExit(f"No encuentro la historia {ident}")
    pend = historias.siguientes(set(reg["videos"]))
    if not pend: raise SystemExit("No quedan historias pendientes.")
    return pend[0]


def cmd_lote(cfg, args):
    from . import video, youtube
    lock = os.path.join(cfg["carpeta_datos"], "lote.lock")
    if os.path.exists(lock) and (dt.datetime.now().timestamp() - os.path.getmtime(lock)) < 3 * 3600:
        print("Ya hay un lote en marcha; salgo."); return
    open(lock, "w").close()
    try:
        reg = leer_registro(cfg)
        libres = huecos(cfg, reg, dt.datetime.now(dt.timezone.utc))
        if args.max: libres = libres[:args.max]
        if not libres:
            log(cfg, "Nada que hacer: todos los huecos de las próximas horas ya están programados."); return
        log(cfg, f"Huecos por rellenar: {', '.join(s.strftime('%d/%m %H:%M') for s in libres)}")
        for slot in libres:
            # Reutiliza un video ya renderizado que no se pudo subir; si no, la siguiente historia.
            pend_subida = [k for k, v in reg["videos"].items() if not v.get("youtube_id") and v.get("mp4") and os.path.exists(v["mp4"])
                          and (cfg["subir_a_youtube"] and not args.sin_subir or not v.get("reservado"))]
            if pend_subida:
                hid = pend_subida[0]; h = json.load(open(os.path.join(reg["videos"][hid]["carpeta"], "historia.json"), encoding="utf-8"))
            else:
                cola = historias.siguientes(set(reg["videos"]))
                if not cola:
                    log(cfg, "⚠️ No quedan historias en la cola (haz git pull o espera a que lleguen más)."); break
                h = cola[0]; hid = h["id"]
                log(cfg, f"Renderizando {hid}...")
                carpeta = video.renderizar(h, cfg)
                reg["videos"][hid] = {"carpeta": carpeta, "mp4": os.path.join(carpeta, f"{hid}.mp4"), "titulo": h["titulo"],
                                      "renderizado_en": dt.datetime.now().isoformat(timespec="seconds")}
                guardar_registro(cfg, reg)
            v = reg["videos"][hid]
            meta = metadatos.generar(h)
            with open(os.path.join(v["carpeta"], "metadatos.json"), "w", encoding="utf-8") as f: json.dump(meta, f, ensure_ascii=False, indent=1)
            if not cfg["subir_a_youtube"] or args.sin_subir:
                # Reserva el hueco para no generar más videos de la cuenta; se subirá cuando se active la subida.
                v["reservado"] = slot.isoformat(); guardar_registro(cfg, reg)
                log(cfg, f"Listo (sin subir): {v['mp4']}"); continue
            try:
                yid = youtube.subir(cfg, v["mp4"], meta, publicar_en=slot, miniatura=os.path.join(v["carpeta"], "miniatura.png"))
            except youtube.CuotaAgotada:
                log(cfg, "Cuota diaria de YouTube agotada. Lo reintento en la próxima ejecución."); break
            v.update(youtube_id=yid, publicar_en=slot.isoformat(), subido_en=dt.datetime.now().isoformat(timespec="seconds"))
            guardar_registro(cfg, reg)
            log(cfg, f"Subido {hid} -> https://youtube.com/shorts/{yid} (se publica {slot:%d/%m %H:%M})")
        quedan = len(historias.siguientes(set(reg["videos"])))
        if quedan < len(cfg["horas_publicacion"]) * 2:
            log(cfg, f"Aviso: solo quedan {quedan} historias en cola.")
    finally:
        try: os.remove(lock)
        except OSError: pass


def cmd_estado(cfg, args):
    reg = leer_registro(cfg)
    prog = sorted((v["publicar_en"], k, v.get("youtube_id")) for k, v in reg["videos"].items() if v.get("publicar_en"))
    print("Programados / publicados:")
    for p, k, y in prog[-20:]: print(f"  {p[:16].replace('T', ' ')}  {k}  https://youtube.com/shorts/{y}")
    cola = historias.siguientes(set(reg["videos"]))
    print(f"\nHistorias en cola: {len(cola)}")
    for h in cola[:10]: print(f"  {h['id']}: {h['titulo']}")


def cmd_comprobar(cfg, args):
    ok = True
    print(f"Carpeta de videos: {cfg['carpeta_salida']}\nCarpeta de datos:  {cfg['carpeta_datos']}\nFuente: {cfg['fuente']}")
    for mod in ["cairo", "kokoro_onnx", "soundfile", "numpy", "PIL", "resvg_py", "imageio_ffmpeg", "googleapiclient", "google_auth_oauthlib"]:
        try: __import__(mod); print(f"  ✔ {mod}")
        except Exception as e: ok = False; print(f"  ✘ {mod}: {e}")
    try:
        from zoneinfo import ZoneInfo; ZoneInfo(cfg["zona_horaria"]); print(f"  ✔ zona horaria {cfg['zona_horaria']}")
    except Exception as e: ok = False; print(f"  ✘ zona horaria: {e} (pip install tzdata)")
    try:
        n = len(historias.todas()); print(f"  ✔ {n} historias válidas")
    except Exception as e: ok = False; print(f"  ✘ historias: {e}")
    from .voz import descargar_modelos
    descargar_modelos(os.path.join(cfg["carpeta_datos"], "modelos")); print("  ✔ modelos de voz")
    for nombre in ("client_secret.json", "token.json"):
        p = os.path.join(cfg["carpeta_datos"], nombre)
        print(f"  {'✔' if os.path.exists(p) else '·'} {nombre} {'' if os.path.exists(p) else '(falta)'}")
    print("\nTodo bien." if ok else "\nHay que arreglar lo marcado con ✘.")


def main():
    ap = argparse.ArgumentParser(prog="datocurioso", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("comprobar"); sub.add_parser("autorizar"); sub.add_parser("estado")
    for n in ("previa", "render"):
        p = sub.add_parser(n); p.add_argument("id", nargs="?")
    p = sub.add_parser("lote"); p.add_argument("--sin-subir", action="store_true"); p.add_argument("--max", type=int)
    args = ap.parse_args()
    cfg = config.cargar()
    try:
        if args.cmd == "comprobar": cmd_comprobar(cfg, args)
        elif args.cmd == "autorizar":
            from . import youtube; youtube.autorizar(cfg)
        elif args.cmd == "estado": cmd_estado(cfg, args)
        elif args.cmd in ("previa", "render"):
            from . import video
            h = buscar(cfg, args.id)
            print(video.renderizar(h, cfg, solo_previa=args.cmd == "previa"))
        elif args.cmd == "lote": cmd_lote(cfg, args)
    except SystemExit:
        raise
    except Exception:
        log(cfg, "ERROR:\n" + traceback.format_exc()); sys.exit(1)


if __name__ == "__main__":
    main()
