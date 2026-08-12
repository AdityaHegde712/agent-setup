import io
import base64
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from PIL import Image


def test_select_vlm_model() -> None:
    from mcp_servers.vlm_server.server import select_vlm_model

    low_vram_model = select_vlm_model(4500, threshold_mb=5000)
    assert low_vram_model == "qwen2.5vl:3b"

    high_vram_model = select_vlm_model(6500, threshold_mb=5000)
    assert high_vram_model == "qwen2.5vl:7b"


def test_get_max_pixels() -> None:
    from mcp_servers.vlm_server.server import get_max_pixels

    assert get_max_pixels("qwen2.5vl:3b") == 1_300_000
    assert get_max_pixels("qwen2.5vl:7b") == 4_194_304


def test_process_and_encode_image_downscale(tmp_path: Path) -> None:
    from mcp_servers.vlm_server.server import process_and_encode_image

    large_img_path = tmp_path / "large_screenshot.png"
    img = Image.new("RGB", (2560, 1600), color="blue")
    img.save(large_img_path)

    b64_str = process_and_encode_image(large_img_path, max_pixels=1_300_000)
    img_data = base64.b64decode(b64_str)
    decoded_img = Image.open(io.BytesIO(img_data))

    total_pixels = decoded_img.width * decoded_img.height
    assert total_pixels <= 1_300_000
    assert decoded_img.width < 2560
    assert decoded_img.height < 1600


def test_describe_image_mocked(tmp_path: Path) -> None:
    from mcp_servers.vlm_server.server import describe_image

    img_path = tmp_path / "test_sample.png"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "This is a red square."}

    with patch("pynvml.nvmlDeviceGetMemoryInfo") as mock_nvml, \
         patch("httpx.post", return_value=mock_response) as mock_post:
        
        mock_mem = MagicMock()
        mock_mem.free = 6000 * 1024 * 1024
        mock_nvml.return_value = mock_mem

        res = describe_image(str(img_path))
        assert "This is a red square." in res
        
        cache_file = tmp_path / "test_sample.md"
        assert cache_file.exists()
        assert cache_file.read_text(encoding="utf-8") == "This is a red square."


def test_vlm_server_logging(tmp_path: Path) -> None:
    from mcp_servers.vlm_server.server import log_vlm_event

    log_file = tmp_path / ".cache" / "vlm_server.log"
    log_vlm_event("Test log message", level="INFO", custom_log_file=log_file)

    assert log_file.exists()
    assert "Test log message" in log_file.read_text(encoding="utf-8")


def test_missing_image_file() -> None:
    from mcp_servers.vlm_server.server import describe_image

    with pytest.raises(FileNotFoundError):
        describe_image("non_existent_image.png")
