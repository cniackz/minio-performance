
# MinIO Performance (GitHub Actions)

Repo para medir velocidad de MinIO (upload/download) usando el SDK oficial de Python dentro de GitHub runners.

## ¿Qué hace?

- Lanza un servidor MinIO local
- Usa Python SDK (`minio`) para subir y bajar archivos
- Mide tiempo de operación (en segundos)

## Cómo correr

1. Ve a la pestaña [Actions](../../actions)
2. Ejecuta el workflow `MinIO Speed Test`

## Archivos clave

- `benchmark.py`: script de prueba
- `deploy_minio.sh`: arranca MinIO
- `.github/workflows/benchmark.yml`: workflow de GitHub Actions

## Ejemplo de salida

```

Upload 10MB: 1.12s
Download 10MB: 0.89s

```
