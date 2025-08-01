from minio import Minio
import time, io, statistics, requests

client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
)

bucket = "bench-loop"
object_name = "testfile-1GB"
object_size = 1024 * 1024 * 1024  # 1 GB
data = b"x" * object_size

# Get MinIO version
try:
    r = requests.get("http://localhost:9000/minio/version")
    version = r.json().get("version", "unknown")
except Exception as e:
    version = f"unknown ({e})"

# Setup bucket
if not client.bucket_exists(bucket):
    client.make_bucket(bucket)

upload_times = []
download_times = []

for _ in range(1000):
    # Upload
    start = time.time()
    client.put_object(bucket, object_name, io.BytesIO(data), object_size)
    upload_times.append(time.time() - start)

    # Download
    start = time.time()
    response = client.get_object(bucket, object_name)
    _ = response.read()
    response.close()
    download_times.append(time.time() - start)

# Final summary
print(f"File Size: 1GB")
print(f"MinIO Version: {version}")
print(f"Average PUT: {statistics.mean(upload_times):.2f}s")
print(f"Average GET: {statistics.mean(download_times):.2f}s")
