# Edwar y Hary: 3 meses

Animacion romantica de 54 segundos, dibujada en Python con Pillow y codificada con FFmpeg a traves de `imageio-ffmpeg`. Abre con la portada de cuento y pasa directamente al picnic en el jardin, sin fotos externas. Edwar y Hary conversan, se toman de las manos, se abrazan, se besan y salen juntos; Tommy, un gato blanco con su nombre en el collar, los sigue. El cierre muestra la dedicatoria de sus tres meses.

El jardin es una ilustracion por capas con arco de rosas y glicinias, macizos de flores, manta, platos, tarta, galletas, fruta, bebidas, luces titilantes, petalos, luciernagas y corazones. No se necesita ni se carga `recuerdo_edwar_hary.png`.

## Instalar y generar

Desde esta carpeta, en PowerShell:

```powershell
py -m pip install -r requirements.txt
py animacion.py
```

Se generan:

- `jardin_romantico.mp4`: 1280 x 720, 16:9, 54 segundos, 24 fps.
- `jardin_romantico_vertical.mp4`: 720 x 1280, con el encuadre acercado al picnic para celular.
- `vista_previa.gif`: 400 x 225, 5 fps, paleta compartida; version ligera para revisar la historia.

El proyecto se verifico con Python 3.14.7, Pillow 12.3 y FFmpeg 7.1 incluido por `imageio-ffmpeg`. No hace falta una pagina web ni instalar FFmpeg globalmente.

## Personalizar

Edita `CONFIG`, al principio de `animacion.py`:

- `edwar` y `partner`: nombres, colores y siluetas de cabello/ropa editables; son valores de ilustracion, no una descripcion de rasgos reales.
- `tommy`: pelaje blanco, marcas tenues y color de ojos.
- `colors`: paleta del cielo, jardin, flores, manta y luces.
- `duration_seconds`, `fps`, `landscape_size` y `portrait_size`: duracion, ritmo y formatos.
- `make_gif_preview`: activar o desactivar la vista GIF.
- `gif_size`, `gif_fps` y `gif_colors`: ajustar el tamano y el peso del GIF.

Para ajustar los tiempos de la portada, picnic y cierre, modifica `PICNIC_START`, `WALK_START` y `CLOSING_START` en `animacion.py`. Las frases y sus tiempos estan en `draw_picnic_scene`; el paseo final se dibuja en `draw_walking_scene`. La ilustracion esta en `draw_background` y `draw_picnic`; el texto final se define en `draw_closing`.