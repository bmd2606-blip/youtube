# The Gentlemen — animación

Vídeo de 22 s (1920×1080): intro con título, galería de 5 imágenes con Ken Burns y rótulos, y cierre.

## Poner tus imágenes

Sustituye los marcadores de `assets/imagenes/` por tus capturas **con el mismo nombre**:

| Archivo | Rótulo |
| --- | --- |
| `escena-1.jpg` | Eddie Horniman |
| `escena-2.jpg` | Susie Glass |
| `escena-3.jpg` | Freddy Horniman |
| `escena-4.jpg` | Stanley Glass |
| `escena-5.jpg` | Halstead Manor |

Mejor en horizontal 16:9 (1920×1080 o mayor). Los textos se cambian en `index.html` (`<h2>` y `<p>` de cada `.shot`).

## Renderizar

```bash
npx hyperframes@0.8.79 check
npx hyperframes@0.8.79 render -o renders/the-gentlemen.mp4
```
