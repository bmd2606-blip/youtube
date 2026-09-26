# YouTube — animaciones con HyperFrames

Este repo usa [HyperFrames](https://github.com/heygen-com/hyperframes) (HTML + GSAP → MP4) para crear animaciones de vídeo.

- Proyecto de composición: `animaciones/` (lee `animaciones/CLAUDE.md` antes de tocar nada).
- Skills de HyperFrames versionadas en `.claude/skills/` — empieza siempre por `/hyperframes`.
- `.claude/hooks/session-start.sh` instala FFmpeg y Chrome headless en sesiones web.

## Flujo rápido

```bash
cd animaciones
npx hyperframes check                          # lint + runtime + layout + contraste
npx hyperframes render -o renders/video.mp4    # render a MP4 (renders/ está en .gitignore)
npx hyperframes render --format gif -o renders/video.gif
```

## Reglas de este entorno

- **Sin CDN en el render**: el Chrome headless no puede salir a `cdn.jsdelivr.net` desde el
  contenedor. Carga GSAP desde `assets/vendor/gsap.min.js` (ruta relativa), no desde el CDN.
  Si necesitas otra librería, vendorízala en `animaciones/assets/vendor/` con
  `npm pack <paquete>@<versión>` y extrae el archivo `dist/`.
- Para renderizar un subproyecto nuevo: `npx hyperframes init <nombre> --non-interactive`
  y cambia su `<script src>` de GSAP al archivo local.
- Actualizar skills: `npx hyperframes skills update` y copia las carpetas nuevas de
  `~/.claude/skills/` a `.claude/skills/`.
