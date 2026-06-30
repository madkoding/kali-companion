# Kali — Opciones de empaquetado y distribución

## Estado actual

| Formato | Estado |
|---|---|
| **Docker** | Completo y funcional (`docker/Dockerfile`, `docker/Dockerfile.gpu`) |
| **Electron (AppImage/deb)** | Parcial — `kali-shell/electron-builder.yml` define targets, pero solo empaqueta el shell Electron, **no incluye kali-core (Python)** ni kali-web |
| **pip install** | Funciona — `kali-core` es un paquete Python válido con `pyproject.toml` (hatchling) |
| **Snap/Flatpak** | No existe |

## Componentes del sistema

- **kali-core** — Backend Python (FastAPI + WebSocket). Entry point: `python -m kali_core`
- **kali-web** — Frontend React (Vite). Build: `npm run build` → `dist/`
- **kali-shell** — Shell Electron (opcional, para modo escritorio)
- **qwen-cpp/tts-server** — Binario C++ para Qwen3 TTS (CPU/GPU)
- **Modelos** — Vosk STT (~85 MB), Piper voices (~25 MB), Qwen3 GGUF (~1-2 GB)

## Opciones de empaquetado

### 1. AppImage / Deb (via electron-builder)

- Ya parcialmente configurado en `kali-shell/electron-builder.yml`
- Problema: electron-builder no empaqueta Python. Hay que bundlear un venv con todas las dependencias
- Tamaño estimado: ~500 MB+ (Python + pip deps + modelos)
- Ideal para: escritorio Linux

```yaml
# Configuración existente en kali-shell/electron-builder.yml
appId: com.kalicompanion.shell
productName: Kali
linux:
  target:
    - AppImage
    - deb
  category: Utility
```

### 2. Tarball con venv + script de instalación

- Crear un script que: instale Python 3.12, cree un venv, instale kali-core + deps, descargue modelos, instale systemd service
- Más simple, menos frágil que PyInstaller
- Tamaño: ~300 MB (sin modelos) o ~1.5 GB (con modelos)

### 3. PyInstaller / Nuitka → binario único

- Congelar kali-core en un solo ejecutable
- Problema: dependencias nativas (numpy, scipy, vosk, webrtcvad) son difíciles de congelar
- Tamaño: ~200-400 MB
- Riesgo medio-alto de romper cosas

### 4. pip + systemd service

- `pip install kali-core` (ya funciona)
- Crear `kali-companion.service` para systemd
- El más limpio pero requiere que el usuario tenga Python 3.12
- Tamaño mínimo: solo el código Python

### 5. Snap / Flatpak

- Aislamiento completo, auto-contenido
- Snap: más fácil de distribuir vía Snap Store
- Flatpak: mejor para ecosistema GNOME
- Ambos necesitan crear configs desde cero
- Tamaño: ~500 MB+ con dependencias

## Recomendación

**Opción 2 (tarball + script)** o **Opción 4 (pip + systemd)** son las más pragmáticas:

- **Opción 2** si querés algo auto-contenido que funcione sin depender del sistema
- **Opción 4** si preferís integración limpia con el sistema (como cualquier paquete Python)

## Dependencias del sistema (runtime)

| Dependencia | Propósito |
|---|---|
| Python 3.12+ | kali-core runtime |
| nginx | Reverse proxy + archivos estáticos (Docker mode) |
| libopenblas0 | BLAS para binario Qwen3 C++ |
| libasound2 / libasound2t64 | Acceso a audio (micrófono + parlantes) |
| libpulse0 + pulseaudio-utils | PulseAudio |
| curl / wget / unzip | Descarga de modelos (primer arranque) |
| build-essential / python3-dev | Solo para compilar webrtcvad durante pip install |

## Archivos clave

| Archivo | Propósito |
|---|---|
| `kali-core/pyproject.toml` | Packaging Python (hatchling, v0.1.0) |
| `kali-shell/electron-builder.yml` | Targets AppImage + deb |
| `docker/Dockerfile` | Build CPU |
| `docker/Dockerfile.gpu` | Build GPU/CUDA |
| `docker/entrypoint.sh` | Orquestador runtime |
| `docker/nginx.conf` | Reverse proxy config |
| `scripts/prod.sh` | Launcher producción |
| `scripts/dev.sh` | Launcher desarrollo |
| `scripts/build-qwen-cpp.sh` | Build binario Qwen3 C++ |
