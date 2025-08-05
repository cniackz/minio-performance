from minio import Minio
import time, io, statistics, sys, os

class FakeStream(io.RawIOBase):
    def __init__(self, size):
        self.remaining = size
    def read(self, n=-1):
        if self.remaining <= 0:
            return b""
        chunk = min(n, self.remaining)
        self.remaining -= chunk
        return b"x" * chunk

# Flush output line by line for GitHub Actions
sys.stdout.reconfigure(line_buffering=True)

client = Minio("localhost:9000", access_key="minioadmin", secret_key="minioadmin", secure=False)

bucket = "bench-loop"
version = os.environ.get("MINIO_VERSION", "unknown")

# Define object size from env (e.g., "1GB", "10GB", "100GB")
size_str = os.environ.get("OBJECT_SIZE", "1GB").upper()
size_map = {"1GB": 1, "10GB": 10, "100GB": 100}
object_size = size_map.get(size_str, 1) * 1024 * 1024 * 1024
object_name = f"testfile-{size_str}"
data = b"x" * (1024 * 1024)  # 1MB buffer reused

# Set number of iterations based on object size
iteration_map = {"1GB": 30, "10GB": 5, "100GB": 1}
total_iterations = iteration_map.get(size_str, 1)

print(f"\nFile Size: {size_str}")
print(f"MinIO Version: {version}")
print(f"Running {total_iterations} iterations...\n")

if not client.bucket_exists(bucket):
    client.make_bucket(bucket)

upload_times, download_times = [], []
for i in range(total_iterations):
    # Upload
    start = time.time()
    stream = io.BufferedReader(FakeStream(object_size))
    client.put_object(bucket, object_name, stream, object_size)
    upload_times.append(time.time() - start)

    # Download
    start = time.time()
    response = client.get_object(bucket, object_name)
    _ = response.read()
    response.close()
    download_times.append(time.time() - start)

    print(f"[{i+1}/{total_iterations}] PUT: {upload_times[-1]:.2f}s, GET: {download_times[-1]:.2f}s")

print(f"\nAverage PUT: {statistics.mean(upload_times):.2f}s")
print(f"Average GET: {statistics.mean(download_times):.2f}s")
