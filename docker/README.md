# Kali — Docker Deployment

Despliegue completo de Kali (kali-core + kali-web) en Docker, con soporte para
múltiples motores TTS/STT y aceleración GPU.

## Requisitos

- **Docker** 24+ ([instalar](https://docs.docker.com/engine/install/))
- **Docker Compose** 2.x (incluido con Docker Desktop, o `docker compose` plugin)
- **nvidia-container-toolkit** (opcional, solo para GPU)
  ([instalar](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html))

## Quick Start

```bash
# 1. Clonar el repo
git clone <repo-url> kali
cd kali

# 2. Configurar variables de entorno
cp docker/.env.example .env
$EDITOR .env

# 3. Construir y levantar
docker compose up -d

# 4. Abrir en el navegador
# http://localhost:8080
```

## Selección de Motores

Todo se configura en el `.env`. No se necesitan flags ni perfiles en la línea
de comandos.

### TTS (Text-to-Speech)

| `KALI_TTS_PROVIDER` | Motor | Modelo | Voces |
|---|---|---|---|
| `inproc` | Piper TTS (in-process) | es_ES-davefx-medium | glados-es, robot-es + efectos |
| `qwen3` | Qwen3-TTS 0.6B CustomVoice | ~605 MB | 9 voces predefinidas |
| `qwen3-voicedesign` | Qwen3-TTS 1.7B VoiceDesign | ~1.2 GB | Voz por descripción de texto |
| `http` | Servicio TTS externo | — | Depende del servicio |

```env
# .env
KALI_TTS_PROVIDER=qwen3
KALI_TTS_VOICE=serena
```

### STT (Speech-to-Text)

| `KALI_STT_PROVIDER` | Motor | Estado |
|---|---|---|
| `vosk` | Vosk STT offline | Disponible |
| `qwen3` | Qwen3 STT | Placeholder (futuro) |

```env
# .env
KALI_STT_PROVIDER=vosk
KALI_STT_LANGUAGE=es
```

### Deshabilitar TTS o STT

```env
# .env
KALI_TTS_ENABLED=false
```

## GPU (CUDA)

Para usar aceleración GPU con Qwen3-TTS o futuros motores STT/ASR:

```bash
# 1. Construir imagen GPU
docker build -f docker/Dockerfile.gpu -t kali:gpu .

# 2. Configurar .env
# KALI_TTS_PROVIDER=qwen3
# KALI_QWEN_BACKEND=CUDA0

# 3. Levantar con override GPU
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

La imagen GPU incluye tanto el binario CUDA como el CPU como fallback.
Si no hay GPU disponible, usa `KALI_QWEN_BACKEND=CPU` para forzar CPU.

## Docker sin Compose

Si prefieres usar solo Docker:

```bash
# Construir
docker build -f docker/Dockerfile -t kali:latest .

# Piper TTS + Vosk STT
docker run -d --name kali \
  -p 8900:8900 -p 8080:80 \
  -v kali-models:/app/models \
  -v kali-data:/app/data \
  --device /dev/snd \
  kali:latest

# Qwen3 TTS + Vosk STT
docker run -d --name kali \
  -p 8900:8900 -p 8080:80 \
  -v kali-models:/app/models \
  -v kali-data:/app/data \
  --device /dev/snd \
  -e KALI_TTS_PROVIDER=qwen3 \
  kali:latest

# Qwen3 TTS con GPU
docker run -d --name kali --gpus all \
  -p 8900:8900 -p 8080:80 \
  -v kali-models:/app/models \
  -v kali-data:/app/data \
  --device /dev/snd \
  -e KALI_TTS_PROVIDER=qwen3 \
  -e KALI_QWEN_BACKEND=CUDA0 \
  kali:gpu
```

## Acceso al Micrófono (STT)

El contenedor necesita acceso al hardware de audio del host:

- **ALSA:** Se monta `/dev/snd` como dispositivo.
- **PulseAudio:** Se monta el socket `${XDG_RUNTIME_DIR}/pulse`.

Si el STT no detecta el micrófono, verifica:

```bash
# Probar ALSA dentro del contenedor
docker exec kali arecord -l

# Probar PulseAudio
docker exec kali pactl info
```

## Variables de Entorno

Todas las variables están documentadas en `docker/.env.example`.
Las más importantes:

| Variable | Default | Descripción |
|---|---|---|
| `KALI_TTS_PROVIDER` | `inproc` | Motor TTS: inproc, qwen3, qwen3-voicedesign, http |
| `KALI_TTS_VOICE` | `glados-es` | Voz por defecto |
| `KALI_STT_PROVIDER` | `vosk` | Motor STT: vosk, qwen3 (futuro) |
| `KALI_STT_LANGUAGE` | `es` | Idioma STT: es, en |
| `KALI_LLM_API_URL` | `http://localhost:11434/v1` | Endpoint LLM (Ollama, OpenAI, etc.) |
| `KALI_LLM_MODEL` | `glm-5.1` | Modelo LLM |
| `KALI_QWEN_BACKEND` | `CPU` | Backend Qwen3: CPU, CUDA0, CUDA1, VULKAN0 |

## Persistencia

| Volumen | Ruta en contenedor | Contenido |
|---|---|---|
| `kali-models` | `/app/models` | Modelos TTS/STT descargados |
| `kali-data` | `/app/data` | SQLite sessions, ai_config.json, snapshots, imágenes |

Los modelos se descargan automáticamente en el primer arranque y se persisten
en el volumen `kali-models`. Arranques posteriores son inmediatos.

## Estructura de la Imagen

```
/app/
├── kali-core/           # Python backend (kali-core)
│   └── kali_core/
│       ├── voice/       # TTS engines
│       ├── ear/         # STT (Vosk)
│       ├── mind/        # Agent + LLM
│       └── ...
├── kali-web/
│   └── dist/            # Frontend compilado (React + Vite)
├── qwen-cpp/
│   └── build/           # Binario tts-server (CPU)
│   └── build-gpu/       # Binario tts-server (CUDA, solo en :gpu)
├── models/              # Modelos descargados (volumen)
├── data/                # Datos persistentes (volumen)
├── scripts/             # Scripts de descarga
└── entrypoint.sh        # Script de arranque
```

## Troubleshooting

### El contenedor no arranca

```bash
# Ver logs
docker compose logs kali

# Verificar health
curl http://localhost:8900/health
```

### Qwen3 no encuentra el binario o modelos

El entrypoint descarga los modelos automáticamente. Si falla:

```bash
# Verificar que el volumen kali-models existe
docker volume ls | grep kali-models

# Forzar re-descarga
docker compose down -v
docker compose up -d
```

### GPU no detectada

```bash
# Verificar nvidia-container-toolkit
nvidia-ctk --version

# Verificar que Docker ve la GPU
docker run --rm --gpus all nvidia/cuda:12.6.0-runtime-ubuntu24.04 nvidia-smi

# Si no funciona, reinstalar nvidia-container-toolkit
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
```

### No se escucha audio / micrófono no funciona

```bash
# Verificar dispositivos ALSA
docker exec kali arecord -l

# Si no aparecen, verificar que /dev/snd está montado
docker inspect kali | grep -A 5 Devices

# Para PulseAudio, verificar el socket
ls -la ${XDG_RUNTIME_DIR}/pulse/native
```

### Ollama no es accesible desde el contenedor

El compose usa `network_mode: host`, por lo que `localhost:11434` debería
funcionar directamente. Si usas Docker sin compose, asegúrate de que el
contenedor pueda alcanzar el host:

```bash
# Con network_mode host
docker run ... --network host ...

# O usa host.docker.internal en vez de localhost
KALI_LLM_API_URL=http://host.docker.internal:11434/v1
```
