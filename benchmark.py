from minio import Minio
import time, io, statistics, sys, os

class FakeStream(io.RawIOBase):
    def __init__(self, size):
        self.remaining = size
    def readable(self):
        return True
    def read(self, n=-1):
        if self.remaining <= 0:
            return b""
        chunk = min(n, self.remaining)
        self.remaining -= chunk
        return b"x" * chunk
    def readinto(self, b):
        if self.remaining <= 0:
            return 0
        chunk = min(len(b), self.remaining)
        b[:chunk] = b"x" * chunk
        self.remaining -= chunk
        return chunk

# Flush output line by line for GitHub Actions
sys.stdout.reconfigure(line_buffering=True)

client = Minio("localhost:9000", access_key="minioadmin", secret_key="minioadmin", secure=False)

bucket = "bench-loop"
version = os.environ.get("MINIO_VERSION", "unknown")
size_str = os.environ.get("OBJECT_SIZE", "1GB").upper()
mode = os.environ.get("MODE", "single-disk").lower()  # <- "multi-disk" or "single-disk"

# Size in bytes
size_map = {"128KB": 128 * 1024, "1MB": 1 * 1024 * 1024, "1GB": 1 * 1024 * 1024 * 1024}
object_size = size_map.get(size_str, 1 * 1024 * 1024)

# Iteration strategy based on mode
if mode == "multi-disk":
    iteration_map = {"128KB": 50, "1MB": 20, "1GB": 2}
else:
    iteration_map = {"128KB": 100, "1MB": 50, "1GB": 10}

total_iterations = iteration_map.get(size_str, 1)
object_name = f"testfile-{size_str}"

print(f"\nFile Size: {size_str}")
print(f"MinIO Version: {version}")
print(f"Running {total_iterations} iterations in mode: {mode}\n")

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

    # 🧹 Clean up
    client.remove_object(bucket, object_name)

    upload_ms = upload_times[-1] * 1000
    download_ms = download_times[-1] * 1000
    print(f"[{i+1}/{total_iterations}] PUT: {upload_ms:.1f}ms, GET: {download_ms:.1f}ms")

print(f"\nAverage PUT: {statistics.mean(upload_times)*1000:.1f}ms")
print(f"Average GET: {statistics.mean(download_times)*1000:.1f}ms")
