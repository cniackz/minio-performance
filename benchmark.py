from minio import Minio
from minio.error import S3Error
import time, io

client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
)

bucket = "bench"

# Crear bucket si no existe
if not client.bucket_exists(bucket):
    client.make_bucket(bucket)

# Crear un objeto de 10MB
data = b"x" * (10 * 1024 * 1024)  # 10MB
object_name = "testfile-10MB"

# Subida
start = time.time()
client.put_object(bucket, object_name, io.BytesIO(data), len(data))
upload_time = time.time() - start
print(f"Upload 10MB: {upload_time:.2f}s")

# Descarga
start = time.time()
response = client.get_object(bucket, object_name)
_ = response.read()
download_time = time.time() - start
print(f"Download 10MB: {download_time:.2f}s")

response.close()
