import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.config import DATA_DIR, DOWNLOADS_DIR, CACHE_DIR, REGISTRY_FILE, DEFAULT_SHEETS
from backend.sheet_parser import (
    extract_sheet_id,
    inspect_workbook,
    parse_sheet_tab
)

logger = logging.getLogger("sheet_repository")
logging.basicConfig(level=logging.INFO)

class SheetRepository:
    def __init__(self):
        self.registry_file = REGISTRY_FILE
        self._ensure_initialized()

    def _ensure_initialized(self):
        """Ensure initial sheets (Link 1 and Link 2) are registered and cached."""
        if not self.registry_file.exists():
            initial_registry = []
            for default in DEFAULT_SHEETS:
                sheet_id = default["id"]
                xlsx_path = DOWNLOADS_DIR / f"{sheet_id}.xlsx"
                
                # If file exists in downloads, inspect and parse
                if xlsx_path.exists():
                    try:
                        tabs_info, rec_tab = inspect_workbook(str(xlsx_path))
                        parsed = parse_sheet_tab(str(xlsx_path), rec_tab)
                        
                        # Cache parsed data
                        cache_path = CACHE_DIR / f"{sheet_id}_{rec_tab.strip().replace(' ', '_')}.json"
                        with open(cache_path, "w", encoding="utf-8") as f:
                            json.dump(parsed, f, ensure_ascii=False)

                        entry = {
                            "id": sheet_id,
                            "url": default["url"],
                            "label": default["label"],
                            "active_tab": rec_tab,
                            "tabs": tabs_info,
                            "total_rows": parsed["total_rows"],
                            "last_synced": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "Ready",
                            "answer_rate": parsed["analytics"].get("answer_rate_pct", 0)
                        }
                        initial_registry.append(entry)
                    except Exception as e:
                        logger.error(f"Error initializing default sheet {sheet_id}: {e}")
                else:
                    # Register entry pending download
                    initial_registry.append({
                        "id": sheet_id,
                        "url": default["url"],
                        "label": default["label"],
                        "active_tab": "",
                        "tabs": [],
                        "total_rows": 0,
                        "last_synced": "Not Synced",
                        "status": "Pending Download",
                        "answer_rate": 0
                    })
            
            self._save_registry(initial_registry)

    def get_registry(self) -> List[Dict[str, Any]]:
        if not self.registry_file.exists():
            return []
        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading registry: {e}")
            return []

    def _save_registry(self, data: List[Dict[str, Any]]):
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def download_sheet(self, sheet_id: str) -> Path:
        """Download Google Sheet as xlsx using export URL."""
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        target_path = DOWNLOADS_DIR / f"{sheet_id}.xlsx"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        resp = requests.get(export_url, headers=headers, allow_redirects=True, timeout=60)
        
        if resp.status_code != 200:
            raise Exception(f"Failed to download Google Sheet (HTTP {resp.status_code}). Ensure link sharing is set to 'Anyone with the link can view'.")
        
        content = resp.content
        if len(content) < 500 or b"<html" in content[:200].lower():
            raise Exception("Google returned an HTML error/login page instead of spreadsheet. Ensure sheet sharing permissions are public/link-accessible.")
            
        with open(target_path, "wb") as f:
            f.write(content)
            
        return target_path

    def add_sheet(self, url_or_id: str, label: Optional[str] = None) -> Dict[str, Any]:
        """Add a new Google Sheet to the repository and process it."""
        sheet_id = extract_sheet_id(url_or_id)
        if not sheet_id:
            raise ValueError("Invalid Google Sheet link or ID provided.")

        registry = self.get_registry()
        existing = next((s for s in registry if s["id"] == sheet_id), None)
        
        xlsx_path = DOWNLOADS_DIR / f"{sheet_id}.xlsx"
        
        # Download if doesn't exist or re-fetching
        try:
            xlsx_path = self.download_sheet(sheet_id)
        except Exception as e:
            if not xlsx_path.exists():
                raise e
            logger.warning(f"Using existing cached xlsx file for {sheet_id} due to network error: {e}")

        # Inspect tabs
        tabs_info, rec_tab = inspect_workbook(str(xlsx_path))
        if not rec_tab:
            raise Exception("No readable sheets/tabs found in this workbook.")

        # Parse recommended tab
        parsed = parse_sheet_tab(str(xlsx_path), rec_tab)

        # Cache parsed data
        cache_key = f"{sheet_id}_{rec_tab.strip().replace(' ', '_')}"
        cache_path = CACHE_DIR / f"{cache_key}.json"
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False)

        sheet_label = label.strip() if label else f"Sheet - {rec_tab}"
        
        entry = {
            "id": sheet_id,
            "url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit?usp=sharing" if not url_or_id.startswith("http") else url_or_id,
            "label": sheet_label,
            "active_tab": rec_tab,
            "tabs": tabs_info,
            "total_rows": parsed["total_rows"],
            "last_synced": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Ready",
            "answer_rate": parsed["analytics"].get("answer_rate_pct", 0)
        }

        if existing:
            # Update existing
            idx = registry.index(existing)
            registry[idx] = entry
        else:
            registry.append(entry)

        self._save_registry(registry)
        return entry

    def sync_sheet(self, sheet_id: str, tab_name: Optional[str] = None) -> Dict[str, Any]:
        """Re-sync and update a registered Google Sheet."""
        registry = self.get_registry()
        entry = next((s for s in registry if s["id"] == sheet_id), None)
        if not entry:
            raise ValueError(f"Sheet {sheet_id} not found in registry.")

        # Download latest
        xlsx_path = self.download_sheet(sheet_id)
        tabs_info, rec_tab = inspect_workbook(str(xlsx_path))
        
        target_tab = tab_name or entry.get("active_tab") or rec_tab
        # Verify target tab exists
        if not any(t["name"] == target_tab for t in tabs_info):
            target_tab = rec_tab

        parsed = parse_sheet_tab(str(xlsx_path), target_tab)

        cache_key = f"{sheet_id}_{target_tab.strip().replace(' ', '_')}"
        cache_path = CACHE_DIR / f"{cache_key}.json"
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False)

        entry["tabs"] = tabs_info
        entry["active_tab"] = target_tab
        entry["total_rows"] = parsed["total_rows"]
        entry["last_synced"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        entry["status"] = "Ready"
        entry["answer_rate"] = parsed["analytics"].get("answer_rate_pct", 0)

        self._save_registry(registry)
        return entry

    def set_active_tab(self, sheet_id: str, tab_name: str) -> Dict[str, Any]:
        """Switch active tab for a sheet and parse it."""
        registry = self.get_registry()
        entry = next((s for s in registry if s["id"] == sheet_id), None)
        if not entry:
            raise ValueError(f"Sheet {sheet_id} not found in registry.")

        xlsx_path = DOWNLOADS_DIR / f"{sheet_id}.xlsx"
        if not xlsx_path.exists():
            xlsx_path = self.download_sheet(sheet_id)

        parsed = parse_sheet_tab(str(xlsx_path), tab_name)

        cache_key = f"{sheet_id}_{tab_name.strip().replace(' ', '_')}"
        cache_path = CACHE_DIR / f"{cache_key}.json"
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False)

        entry["active_tab"] = tab_name
        entry["total_rows"] = parsed["total_rows"]
        entry["answer_rate"] = parsed["analytics"].get("answer_rate_pct", 0)

        self._save_registry(registry)
        return entry

    def delete_sheet(self, sheet_id: str):
        """Remove a sheet from the repository."""
        registry = self.get_registry()
        registry = [s for s in registry if s["id"] != sheet_id]
        self._save_registry(registry)

        # Cleanup cache files for this sheet
        for p in CACHE_DIR.glob(f"{sheet_id}_*.json"):
            try:
                p.unlink()
            except:
                pass

    def get_sheet_data(self, sheet_id: str, tab_name: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve cached parsed data or parse if not yet cached."""
        registry = self.get_registry()
        entry = next((s for s in registry if s["id"] == sheet_id), None)
        if not entry:
            raise ValueError(f"Sheet {sheet_id} not found.")

        target_tab = tab_name or entry.get("active_tab")
        if not target_tab:
            target_tab = entry.get("tabs", [{}])[0].get("name", "")

        cache_key = f"{sheet_id}_{target_tab.strip().replace(' ', '_')}"
        cache_path = CACHE_DIR / f"{cache_key}.json"

        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading cache {cache_path}: {e}")

        # Parse from downloaded xlsx
        xlsx_path = DOWNLOADS_DIR / f"{sheet_id}.xlsx"
        if not xlsx_path.exists():
            xlsx_path = self.download_sheet(sheet_id)

        parsed = parse_sheet_tab(str(xlsx_path), target_tab)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False)
            
        return parsed

    def get_combined_data(self) -> Dict[str, Any]:
        """Aggregate analytics from all active sheets into a combined retro view."""
        registry = self.get_registry()
        if not registry:
            return {"records": [], "analytics": {}, "total_rows": 0, "sheet_count": 0}

        combined_records = []
        poc_map = {}
        status_counts = {}
        gender_counts = {'Male': 0, 'Female': 0, 'Not Specified': 0}
        date_counts = {}
        district_counts = {}
        purpose_counts = {}
        membership_counts = {'Yes': 0, 'No': 0, 'Other': 0}
        donation_counts = {'Yes': 0, 'No': 0, 'Other': 0}
        
        total_calls = 0
        answered_calls = 0
        not_answered_calls = 0

        for entry in registry:
            sheet_id = entry["id"]
            active_tab = entry.get("active_tab")
            if not active_tab:
                continue
            try:
                data = self.get_sheet_data(sheet_id, active_tab)
                analytics = data.get("analytics", {})
                
                total_calls += analytics.get("total_calls", 0)
                answered_calls += analytics.get("answered_calls", 0)
                not_answered_calls += analytics.get("not_answered_calls", 0)

                # Merge POC summaries
                for poc_stat in analytics.get("poc_summary", []):
                    name = poc_stat["poc"]
                    if name not in poc_map:
                        poc_map[name] = {
                            "poc": name,
                            "total": 0,
                            "answered": 0,
                            "not_answered": 0,
                            "male": 0,
                            "female": 0,
                            "membership_yes": 0,
                            "donation_yes": 0
                        }
                    poc_map[name]["total"] += poc_stat.get("total", 0)
                    poc_map[name]["answered"] += poc_stat.get("answered", 0)
                    poc_map[name]["not_answered"] += poc_stat.get("not_answered", 0)
                    poc_map[name]["male"] += poc_stat.get("male", 0)
                    poc_map[name]["female"] += poc_stat.get("female", 0)
                    poc_map[name]["membership_yes"] += poc_stat.get("membership_yes", 0)
                    poc_map[name]["donation_yes"] += poc_stat.get("donation_yes", 0)

                # Merge statuses
                for st, cnt in analytics.get("status_breakdown", {}).items():
                    status_counts[st] = status_counts.get(st, 0) + cnt

                # Merge genders
                for g, cnt in analytics.get("gender_breakdown", {}).items():
                    gender_counts[g] = gender_counts.get(g, 0) + cnt

                # Merge date timeline
                for dt_stat in analytics.get("date_timeline", []):
                    d = dt_stat["date"]
                    if d not in date_counts:
                        date_counts[d] = {"date": d, "total": 0, "answered": 0, "not_answered": 0}
                    date_counts[d]["total"] += dt_stat.get("total", 0)
                    date_counts[d]["answered"] += dt_stat.get("answered", 0)
                    date_counts[d]["not_answered"] += dt_stat.get("not_answered", 0)

                # Merge districts
                for dist in analytics.get("top_districts", []):
                    d_name = dist["district"]
                    district_counts[d_name] = district_counts.get(d_name, 0) + dist["count"]

                # Merge purposes
                for purp in analytics.get("top_purposes", []):
                    p_name = purp["purpose"]
                    purpose_counts[p_name] = purpose_counts.get(p_name, 0) + purp["count"]

                # Merge memberships
                for k, v in analytics.get("membership_summary", {}).items():
                    membership_counts[k] = membership_counts.get(k, 0) + v

                # Merge donations
                for k, v in analytics.get("donation_summary", {}).items():
                    donation_counts[k] = donation_counts.get(k, 0) + v

                # Append records with source sheet tag
                sheet_label = entry.get("label") or sheet_id
                for r in data.get("records", [])[:10000]: # avoid unbounded memory
                    rec_copy = dict(r)
                    rec_copy["sheet_source"] = sheet_label
                    rec_copy["sheet_id"] = sheet_id
                    combined_records.append(rec_copy)

            except Exception as err:
                logger.error(f"Error processing combined sheet {sheet_id}: {err}")

        # Compute answer rates
        poc_list = list(poc_map.values())
        for p in poc_list:
            p["answer_rate"] = round((p["answered"] / p["total"] * 100), 1) if p["total"] > 0 else 0
        poc_list.sort(key=lambda x: x["total"], reverse=True)

        date_timeline = sorted(list(date_counts.values()), key=lambda x: x["date"])
        top_districts = sorted([{"district": k, "count": v} for k, v in district_counts.items()], key=lambda x: x["count"], reverse=True)[:15]
        top_purposes = sorted([{"purpose": k, "count": v} for k, v in purpose_counts.items()], key=lambda x: x["count"], reverse=True)[:10]

        answer_rate_pct = round((answered_calls / total_calls * 100), 1) if total_calls > 0 else 0
        drop_rate_pct = round((not_answered_calls / total_calls * 100), 1) if total_calls > 0 else 0

        combined_analytics = {
            "total_calls": total_calls,
            "answered_calls": answered_calls,
            "not_answered_calls": not_answered_calls,
            "answer_rate_pct": answer_rate_pct,
            "drop_rate_pct": drop_rate_pct,
            "poc_summary": poc_list,
            "status_breakdown": status_counts,
            "gender_breakdown": gender_counts,
            "date_timeline": date_timeline,
            "top_districts": top_districts,
            "top_purposes": top_purposes,
            "membership_summary": membership_counts,
            "donation_summary": donation_counts,
        }

        return {
            "sheet_id": "all",
            "tab_name": "Combined All Sheets",
            "total_rows": total_calls,
            "sheet_count": len(registry),
            "analytics": combined_analytics,
            "records": combined_records
        }

repository = SheetRepository()

