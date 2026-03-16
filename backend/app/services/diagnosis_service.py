"""
DiagnosisService — orchestrates the full diagnosis pipeline.

Pipeline order:
  1. Check cache (skip if force_refresh=True)
  2. Load raw machine data via MachineService
  3. Run diagnosis pipeline (rules → LLM → parse, with fallback)
  4. Store result in cache
  5. Append result to history.json
  6. Return DiagnosisResult

Raises ValueError if machine_id is not found.
"""
import json
import os
from datetime import datetime, timezone
from typing import List

from app.config import settings
from app.diagnosis.pipeline import DiagnosisPipeline
from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResult
from app.services.cache_service import CacheService
from app.services.machine_service import MachineService


class DiagnosisService:
    def __init__(self):
        self._cache = CacheService()
        self._machine_service = MachineService()
        self._pipeline = DiagnosisPipeline()

    def _cache_key(self, machine_id: str) -> str:
        return f"diagnosis:{machine_id}"

    def _history_path(self, machine_id: str) -> str:
        return os.path.join(settings.DATA_DIR, "machines", machine_id, "history.json")

    def _append_to_history(self, result: DiagnosisResult) -> None:
        path = self._history_path(result.machine_id)
        history: List[dict] = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    history = json.load(fh)
            except (json.JSONDecodeError, OSError):
                history = []
        history.append(result.model_dump())
        # Keep last 20 entries
        history = history[-20:]
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(history, fh, indent=2, default=str)
        except OSError:
            pass  # Non-fatal if history write fails

    async def diagnose(self, request: DiagnosisRequest) -> DiagnosisResult:
        machine_id = request.machine_id
        cache_key = self._cache_key(machine_id)

        # Step 1 — cache check
        if not request.force_refresh:
            cached = self._cache.get(cache_key)
            if cached is not None:
                cached.source = "cache"
                return cached

        # Step 2 — load machine data
        raw_data = self._machine_service.get_machine_raw_data(machine_id)
        if raw_data is None:
            raise ValueError(f"Machine '{machine_id}' not found")

        # Step 3 — run pipeline (rules → LLM → parse, with fallback)
        result = await self._pipeline.run(
            machine_id=machine_id,
            raw_data=raw_data,
            include_logs=request.include_logs,
        )

        # Step 4 — cache result
        self._cache.set(cache_key, result)

        # Step 5 — persist to history
        self._append_to_history(result)

        return result
