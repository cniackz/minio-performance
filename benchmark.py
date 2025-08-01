from minio import Minio
import time, io, statistics, requests

client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
)

bucket = "bench-loop"
object_name = "testfile-100MB"
object_size = 100 * 1024 * 1024  # 100 MB
data = b"x" * object_size

# Get MinIO server version
try:
    r = requests.get("http://localhost:9000/minio/version")
    version = r.json().get("version", "unknown")
except Exception as e:
    version = f"unknown ({e})"

print(f"MinIO version: {version}")

# Setup bucket
if not client.bucket_exists(bucket):
    client.make_bucket(bucket)

upload_times = []
download_times = []

for i in range(1000):
    # Upload
    start = time.time()
    client.put_object(bucket, object_name, io.BytesIO(data), object_size)
    upload_time = time.time() - start
    upload_times.append(upload_time)

    # Download
    start = time.time()
    response = client.get_object(bucket, object_name)
    _ = response.read()
    response.close()
    download_time = time.time() - start
    download_times.append(download_time)

    print(f"[{i+1}/1000] Upload: {upload_time:.2f}s | Download: {download_time:.2f}s")

# Summary
def summarize(times, label):
    print(f"\n{label} Summary (1000x 100MB):")
    print(f"  Min: {min(times):.2f}s")
    print(f"  Max: {max(times):.2f}s")
    print(f"  Avg: {statistics.mean(times):.2f}s")
    print(f"  Std: {statistics.stdev(times):.2f}s")

print(f"\n📝 MinIO version tested: {version}")
summarize(upload_times, "Upload")
summarize(download_times, "Download")
