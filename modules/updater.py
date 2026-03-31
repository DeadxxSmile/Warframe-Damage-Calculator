from __future__ import annotations

import json
import lzma
import re
import shutil
import zipfile
from pathlib import Path

import requests

from .app_paths import ensure_app_dirs

KEY_URL = "https://origin.warframe.com/PublicExport/index_en.txt.lzma"
DATA_URL = "https://content.warframe.com/PublicExport/Manifest/"


class DataRefreshError(RuntimeError):
    pass


class WarframeDataUpdater:
    def __init__(self, timeout: int = 60) -> None:
        self.timeout = timeout
        self.paths = ensure_app_dirs()

    def refresh(self) -> dict[str, str | Path]:
        temp = self.paths["temp"]
        for item in temp.iterdir():
            if item.is_file():
                item.unlink()
            else:
                shutil.rmtree(item, ignore_errors=True)

        lzma_path = temp / "index_en.txt.lzma"
        index_path = temp / "index_en.txt"
        self._download(KEY_URL, lzma_path)
        lzma_method = self._expand_lzma(lzma_path, temp)

        if not index_path.exists():
            matches = sorted(temp.glob("*.txt"))
            if matches:
                index_path = matches[0]
        if not index_path.exists():
            raise DataRefreshError("Could not find the extracted index_en.txt file after decompressing the manifest index.")

        manifest_entries = index_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        needed = {
            "ExportWeapons_en.json": None,
            "ExportUpgrades_en.json": None,
        }
        for entry in manifest_entries:
            for target in list(needed.keys()):
                if entry.startswith(target + "!"):
                    needed[target] = entry

        missing = [name for name, entry in needed.items() if not entry]
        if missing:
            raise DataRefreshError(f"Could not find these files in the manifest: {', '.join(missing)}")

        downloaded: dict[str, Path] = {}
        for logical_name, manifest_name in needed.items():
            target_path = temp / logical_name
            self._download(DATA_URL + manifest_name, target_path)
            downloaded[logical_name] = target_path

        weapons_clean = self._clean_json(downloaded["ExportWeapons_en.json"])
        upgrades_clean = self._clean_json(downloaded["ExportUpgrades_en.json"])

        weapons_zip = self.paths["source"] / "ExportWeapons_en_Cleaned.zip"
        upgrades_zip = self.paths["source"] / "ExportKeys_en_Cleaned.zip"

        self._write_zip(weapons_zip, "ExportWeapons_en_Cleaned.json", weapons_clean)
        self._write_zip(upgrades_zip, "ExportUpgrades_en_Cleaned.json", upgrades_clean)

        return {
            "weapons_zip": weapons_zip,
            "upgrades_zip": upgrades_zip,
            "lzma_method": lzma_method,
        }

    def update_and_build_database(
        self,
        db_path: str | Path,
        cleaned_weapons_zip_path: str | Path,
        cleaned_upgrades_zip_path: str | Path,
        spreadsheet_xlsx_path: str | Path | None = None,
        allow_bundled_fallback: bool = True,
    ) -> dict[str, str | Path | None]:
        from .importer import build_database

        weapons_zip = Path(cleaned_weapons_zip_path)
        upgrades_zip = Path(cleaned_upgrades_zip_path)
        spreadsheet_path = Path(spreadsheet_xlsx_path) if spreadsheet_xlsx_path else None

        refresh_error: str | None = None
        source_mode = "bundled backup"
        lzma_method = "Bundled backup data"

        if allow_bundled_fallback:
            try:
                refresh_outputs = self.refresh()
                weapons_zip = Path(refresh_outputs["weapons_zip"])
                upgrades_zip = Path(refresh_outputs["upgrades_zip"])
                lzma_method = str(refresh_outputs.get("lzma_method") or lzma_method)
                source_mode = "fresh DE data"
            except Exception as exc:
                refresh_error = str(exc)
                if not weapons_zip.exists() or not upgrades_zip.exists():
                    raise DataRefreshError(
                        "WDC could not download fresh data from DE, and bundled backup data was not available.\n\n"
                    )
        else:
            if not weapons_zip.exists() or not upgrades_zip.exists():
                raise DataRefreshError(
                    "Bundled backup data was not found. WDC could not rebuild the database offline."
                )

        build_database(
            db_path=db_path,
            cleaned_weapons_zip_path=weapons_zip,
            cleaned_upgrades_zip_path=upgrades_zip,
            spreadsheet_xlsx_path=spreadsheet_path,
        )

        return {
            "db_path": Path(db_path),
            "weapons_zip": weapons_zip,
            "upgrades_zip": upgrades_zip,
            "source_mode": source_mode,
            "lzma_method": lzma_method,
            "refresh_error": refresh_error,
        }

    def _download(self, url: str, target_path: Path, min_expected_size: int = 0) -> int:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
            "Connection": "keep-alive",
        }

        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                total_bytes = 0
                with requests.get(url, headers=headers, stream=True, timeout=self.timeout) as response:
                    response.raise_for_status()
                    expected_length_header = response.headers.get("Content-Length")
                    expected_length = int(expected_length_header) if expected_length_header and expected_length_header.isdigit() else None

                    with open(target_path, "wb") as handle:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                handle.write(chunk)
                                total_bytes += len(chunk)

                if expected_length is not None and total_bytes != expected_length:
                    raise DataRefreshError(
                        f"Downloaded file size did not match Content-Length for {url}. "
                        f"Expected {expected_length} bytes, got {total_bytes}."
                    )

                if min_expected_size and total_bytes < min_expected_size:
                    raise DataRefreshError(
                        f"Downloaded file was too small for {url}. "
                        f"Expected at least {min_expected_size} bytes, got {total_bytes}."
                    )

                return total_bytes
            except Exception as exc:
                last_error = exc
                if target_path.exists():
                    target_path.unlink(missing_ok=True)

        raise DataRefreshError(f"Failed to download {url}: {last_error}")

    def _expand_lzma(self, input_path: Path, output_path: Path) -> str:
        target_path = output_path / "index_en.txt"
        compressed_bytes = input_path.read_bytes()

        try:
            decompressed_bytes = lzma.decompress(compressed_bytes, format=lzma.FORMAT_ALONE)
            target_path.write_bytes(decompressed_bytes)
            return "Python FORMAT_ALONE"
        except lzma.LZMAError:
            pass

        trimmed_bytes = self._decompress_lzma_trimmed(compressed_bytes)
        target_path.write_bytes(trimmed_bytes)
        return "Python trimmed LZMA recovery"

    def _decompress_lzma_trimmed(self, data: bytes) -> bytes:
        length = len(data)
        last_error: Exception | None = None

        while length > 0:
            try:
                return self._decompress_lzma_streams(data[:length])
            except lzma.LZMAError as exc:
                last_error = exc
                length -= 1

        raise DataRefreshError(
            "Python could not decompress Warframe's manifest index. "
            "Tried direct FORMAT_ALONE and trimmed stream recovery.\n\n"
            f"Last error: {last_error}"
        )

    def _decompress_lzma_streams(self, data: bytes) -> bytes:
        results: list[bytes] = []
        while True:
            decomp = lzma.LZMADecompressor(lzma.FORMAT_AUTO, None, None)
            try:
                res = decomp.decompress(data)
            except lzma.LZMAError:
                if results:
                    break
                raise
            results.append(res)
            data = decomp.unused_data
            if not data:
                break
            if not decomp.eof:
                raise lzma.LZMAError(
                    "Compressed data ended before the end-of-stream marker was reached"
                )
        return b"".join(results)

    def _clean_json(self, json_path: Path) -> dict:
        text = json_path.read_text(encoding="utf-8", errors="ignore")
        cleaned = re.sub(r"\s*\\r\s*", r"\\r", text)
        cleaned = re.sub(r"\s*\\n\s*", r"\\n", cleaned)
        data = json.loads(cleaned)
        if json_path.name == "ExportWeapons_en.json":
            for weapon in data.get("ExportWeapons", []):
                if isinstance(weapon, dict):
                    self._dedupe_key_in_order(weapon, "masteryReq")
        return data

    def _dedupe_key_in_order(self, row: dict, key_name: str) -> None:
        seen = False
        for key in list(row.keys()):
            if key != key_name:
                continue
            if seen:
                del row[key]
            else:
                seen = True

    def _write_zip(self, zip_path: Path, member_name: str, data: dict) -> None:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(member_name, json.dumps(data, indent=4))
