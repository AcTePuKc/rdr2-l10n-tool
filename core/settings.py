from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json

@dataclass
class AppSettings:
    input_dir: str = "01_input_raw_txt"
    master_path: str = "02_master/master.tsv"
    chunks_dir: str = "03_chunks"
    output_dir: str = "04_output_txt"
    norm_mode: str = "safe"
    chunk_size: int = 1000
    separate_global: bool = True
    run_sanity: bool = True

def settings_path() -> Path:
    return Path.cwd() / "settings.json"

def load_settings() -> AppSettings:
    p = settings_path()
    if not p.exists():
        return AppSettings()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return AppSettings(**{**AppSettings().__dict__, **data})
    except Exception:
        return AppSettings()

def save_settings(s: AppSettings) -> None:
    settings_path().write_text(json.dumps(asdict(s), ensure_ascii=False, indent=2), encoding="utf-8")
