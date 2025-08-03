from minio import Minio
import time, io, statistics, requests, sys, os

# Flush output line by line for GitHub Actions
sys.stdout.reconfigure(line_buffering=True)

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
version = os.environ.get("MINIO_VERSION", "unknown")

print(f"\nFile Size: 1GB")
print(f"MinIO Version: {version}")

# Setup bucket
if not client.bucket_exists(bucket):
    client.make_bucket(bucket)

# Target total duration in seconds
target_duration_sec = 20 * 60  # 20 minutes
avg_iteration_time = 3.2  # Estimated seconds per PUT+GET
total_iterations = int(target_duration_sec / avg_iteration_time)

upload_times = []
download_times = []
heartbeat_interval = 60  # seconds
last_heartbeat = time.time()

for i in range(total_iterations):
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

    # Emit heartbeat every minute
    now = time.time()
    if now - last_heartbeat >= heartbeat_interval:
        avg_put = statistics.mean(upload_times)
        avg_get = statistics.mean(download_times)
        print(f"Still running... [{i+1}/{total_iterations}] Average PUT: {avg_put:.2f}s, GET: {avg_get:.2f}s")
        last_heartbeat = now

# Final summary
print(f"Average PUT: {statistics.mean(upload_times):.2f}s")
print(f"Average GET: {statistics.mean(download_times):.2f}s")
