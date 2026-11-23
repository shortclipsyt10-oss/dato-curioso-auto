# Dato Curioso: canal automático de shorts

Pipeline que convierte historias curiosas en shorts verticales (1080x1920, ~1 min) y los publica solos en YouTube:

1. **Historias** (`historias/pendientes/*.json`): guion por escenas, título, descripción, hashtags, fuentes y nota de veracidad. Las escribe Claude y llegan al repo solas cada día.
2. **Video** (`datocurioso/video.py`): voz Kokoro (local y gratis), animación con Cairo y emojis Twemoji, subtítulos palabra a palabra, música generada por código y miniatura.
3. **Publicación** (`datocurioso/youtube.py`): sube cada video a YouTube programado (`publishAt`) en los huecos de `horas_publicacion`.
4. **Tarea de Windows** (`scripts/ejecutar.ps1`): cada 3 horas hace `git pull` y rellena los huecos de las próximas 24 h. Basta con que el PC esté encendido un rato al día.

Los videos terminados quedan en `Escritorio\curiosidades\<id>\` (MP4, miniatura, guion y metadatos) y el historial en `Escritorio\curiosidades\registro.json` y `registro.log`.

## Instalación en Windows

```powershell
git clone https://github.com/shortclipsyt10-oss/dato-curioso-auto.git $HOME\dato-curioso-auto
cd $HOME\dato-curioso-auto
powershell -ExecutionPolicy Bypass -File scripts\instalar.ps1
```

Necesitas Python 3.10–3.13 (`winget install Python.Python.3.12`) y Git (`winget install Git.Git`).

## Conectar YouTube (solo una vez)

Las credenciales **nunca** se suben al repo: viven en `C:\Users\<tú>\.dato-curioso\`.

1. Entra en <https://console.cloud.google.com/> con la cuenta de Google del canal y crea un proyecto llamado `Dato Curioso`.
2. En **APIs y servicios → Biblioteca**, busca **YouTube Data API v3** y pulsa **Habilitar**.
3. En **Google Auth Platform** (antes "Pantalla de consentimiento de OAuth"):
   - Tipo de usuario: **Externo**. Nombre de la app: `Dato Curioso`. Pon tu email de contacto.
   - En **Público**, añade tu cuenta como usuario de prueba y después pulsa **Publicar app** para pasarla a **En producción**. Si la dejas en "Prueba", el permiso caduca cada 7 días y la subida automática se para.
4. En **Clientes** (o **Credenciales → Crear credenciales → ID de cliente de OAuth**): tipo **App de escritorio**, nombre `dato-curioso-pc`. Descarga el JSON, renómbralo a `client_secret.json` y guárdalo en `C:\Users\<tú>\.dato-curioso\client_secret.json`.
5. En la carpeta del repo ejecuta:
   ```powershell
   .venv\Scripts\python -m datocurioso autorizar
   ```
   Se abre el navegador. Elige la cuenta (o la cuenta de marca) del canal. Verás "Google no ha verificado esta app": es tu propia app, pulsa **Configuración avanzada → Ir a Dato Curioso** y acepta. Al terminar, la consola muestra el nombre del canal.

### Límites de la API de YouTube (importante)

- **Videos privados hasta la auditoría.** Google bloquea en privado los videos subidos por API desde proyectos nuevos sin auditar. Para quitar el bloqueo hay que rellenar el formulario gratuito *YouTube API Services – Audit and Quota Extension*: <https://support.google.com/youtube/contact/yt_api_form>. Explica que es una herramienta interna que sube los shorts de tu propio canal.
- **Cuota.** Cada subida cuesta ~1.600 unidades y la cuota diaria por defecto es 10.000, así que caben **6 subidas al día**. Pide **20.000 unidades/día** en el mismo formulario. Cuando la aprueben, cambia `horas_publicacion` en `config.json` por la lista `_horas_cuando_amplien_cuota` (8 al día, una cada 3 horas).
- **Miniaturas.** La API solo deja poner miniatura personalizada si el canal está verificado por teléfono (<https://www.youtube.com/verify>). En los Shorts YouTube a veces muestra igualmente un fotograma del video.

## Comandos

```text
python -m datocurioso comprobar   revisa instalación, modelos y credenciales
python -m datocurioso autorizar   conecta el canal de YouTube
python -m datocurioso previa ID   imagen con todas las escenas (rápido)
python -m datocurioso render ID   genera el video sin subirlo
python -m datocurioso lote        lo que hace la tarea programada (--sin-subir para solo generar)
python -m datocurioso estado      lo programado y lo que queda en cola
```

## Formato de las historias

Ver [`historias/FORMATO.md`](historias/FORMATO.md).

## Créditos

Emojis: [Twemoji](https://github.com/jdecked/twemoji), CC-BY 4.0 (se acredita en cada descripción). Voz: [Kokoro](https://github.com/thewh1teagle/kokoro-onnx).
