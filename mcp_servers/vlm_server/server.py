import base64
from datetime import datetime
import io
import math
import os
from pathlib import Path
import sys
import time
import httpx
from PIL import Image
from mcp.server.mcpserver import MCPServer


mcp = MCPServer("VLM-Tools")


def log_vlm_event(message: str, level: str = "INFO", custom_log_file: Path | None = None) -> None:
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] [{level}] {message}\n"
    sys.stderr.write(log_line)

    if custom_log_file is not None:
        log_path = custom_log_file
    else:
        user_home = Path(os.environ.get("USERPROFILE", os.environ.get("HOME", ".")))
        log_path = user_home / ".config" / "opencode" / ".cache" / "vlm_server.log"

    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(log_line)
    except OSError:
        pass


def get_free_vram_mb() -> int:
    try:
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            return int(info.free // (1024 * 1024))
        except ImportError:
            import nvidia_smi
            nvidia_smi.nvmlInit()
            handle = nvidia_smi.nvmlDeviceGetHandleByIndex(0)
            info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
            return int(info.free // (1024 * 1024))
    except Exception as exc:
        log_vlm_event(f"NVML VRAM check failed: {exc}", level="WARNING")
        return 4000


def select_vlm_model(free_vram_mb: int, threshold_mb: int = 5000) -> str:
    is_gaming_or_low_vram = free_vram_mb < threshold_mb
    if is_gaming_or_low_vram:
        return "qwen2.5vl:3b"

    return "qwen2.5vl:7b"


def get_max_pixels(target_model: str) -> int:
    if target_model == "qwen2.5vl:7b":
        return 4_194_304

    return 1_300_000


def process_and_encode_image(image_path: Path, max_pixels: int = 1_300_000) -> str:
    with Image.open(image_path) as img:
        width, height = img.size
        total_pixels = width * height

        is_exceeding_pixel_limit = total_pixels > max_pixels
        if is_exceeding_pixel_limit:
            scale_factor = math.sqrt(max_pixels / total_pixels)
            new_width = max(1, int(width * scale_factor))
            new_height = max(1, int(height * scale_factor))
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            log_vlm_event(f"Downscaled image from {width}x{height} ({total_pixels/1e6:.2f}MP) to {new_width}x{new_height} ({new_width*new_height/1e6:.2f}MP)")

        buffer = io.BytesIO()
        output_format = img.format if img.format in ["JPEG", "PNG", "WEBP"] else "PNG"
        img.save(buffer, format=output_format)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")


@mcp.tool()
def describe_image(image_path: str, prompt: str = "Describe this image in detail") -> str:
    path_obj = Path(image_path)
    if not path_obj.exists():
        log_vlm_event(f"Image file not found: {image_path}", level="ERROR")
        raise FileNotFoundError(f"Image file not found: {image_path}")

    start_time = time.time()
    log_vlm_event(f"Starting image description for: {image_path}")

    free_vram = get_free_vram_mb()
    target_model = select_vlm_model(free_vram)
    max_pixels = get_max_pixels(target_model)

    log_vlm_event(f"Free VRAM: {free_vram} MB -> Selected Model: {target_model} (Max Pixels Limit: {max_pixels/1e6:.2f}MP)")

    base64_image = process_and_encode_image(path_obj, max_pixels=max_pixels)

    payload = {
        "model": target_model,
        "prompt": prompt,
        "images": [base64_image],
        "stream": False,
        "keep_alive": "5m"
    }

    try:
        response = httpx.post("http://localhost:11434/api/generate", json=payload, timeout=300.0)
        response.raise_for_status()
        result_data = response.json()
        description = result_data.get("response", "").strip()
        elapsed = time.time() - start_time
        log_vlm_event(f"Ollama inference completed successfully in {elapsed:.2f}s using {target_model}")
    except httpx.HTTPError as exc:
        elapsed = time.time() - start_time
        log_vlm_event(f"Ollama VLM API request failed after {elapsed:.2f}s: {exc}", level="ERROR")
        raise RuntimeError(f"Ollama VLM API request failed: {exc}") from exc

    output_md_path = path_obj.with_suffix(".md")

    try:
        output_md_path.write_text(description, encoding="utf-8")
        log_vlm_event(f"Saved image description cache to: {output_md_path}")
    except OSError as err:
        log_vlm_event(f"Failed to write cache file {output_md_path}: {err}", level="WARNING")

    return description


if __name__ == "__main__":
    mcp.run()
