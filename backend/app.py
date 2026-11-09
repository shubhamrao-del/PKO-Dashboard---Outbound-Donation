import csv
import io
import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.config import STATIC_DIR
from backend.repository import repository

logger = logging.getLogger("dashboard_api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Calling Analytics & Operations Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
ADMIN_PASSWORD = "1234"
class AddSheetRequest(BaseModel):
    url: str
    label: Optional[str] = None
    password: Optional[str] = None

class SetTabRequest(BaseModel):
    tab_name: str

@app.get("/api/sheets")
def get_sheets():
    """Return all registered Google Sheets and their metadata."""
    registry = repository.get_registry()
    return {"sheets": registry}

@app.post("/api/sheets")
def add_sheet(req: AddSheetRequest):
    """Add a new Google Sheet URL to the repository."""
    try:
        sheet = repository.add_sheet(req.url, req.label)
        return {"success": True, "sheet": sheet}
    except Exception as e:
        logger.error(f"Error adding sheet: {e}")
        error_msg = str(e)
        if "not well-formed" in error_msg or "syntax error" in error_msg.lower() or "html" in error_msg.lower():
            raise HTTPException(
                status_code=400, 
                detail="Google Sheet is private or format is invalid. Please make sure the sheet is public ('Anyone with the link can view')."
            )
        raise HTTPException(status_code=400, detail=error_msg)
      

@app.post("/api/sheets/{sheet_id}/sync")
def sync_sheet(sheet_id: str, tab_name: Optional[str] = None):
    """Re-sync an existing sheet from Google Sheets."""
    try:
        sheet = repository.sync_sheet(sheet_id, tab_name)
        return {"success": True, "sheet": sheet}
    except Exception as e:
        logger.error(f"Error syncing sheet {sheet_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))



@app.delete("/api/sheets/{sheet_id}")
def delete_sheet(sheet_id: str):
    """Remove a sheet from the repository."""
    try:
        repository.delete_sheet(sheet_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/sheets/{sheet_id}/tab")
def set_active_tab(sheet_id: str, req: SetTabRequest):
    """Switch the active tab for a sheet."""
    try:
        sheet = repository.set_active_tab(sheet_id, req.tab_name)
        return {"success": True, "sheet": sheet}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



def filter_records(
    records: List[dict],
    poc: Optional[str] = None,
    status: Optional[str] = None,
    gender: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None
) -> List[dict]:
    """Helper to apply user filters to records."""
    filtered = records
    
    if poc:
        poc_clean = poc.strip().lower()
        if poc_clean != "all":
            filtered = [r for r in filtered if r.get("poc", "").strip().lower() == poc_clean]
            
    if status:
        st_clean = status.strip().lower()
        if st_clean == "answered":
            filtered = [r for r in filtered if r.get("is_answered") is True]
        elif st_clean == "not answered":
            filtered = [r for r in filtered if r.get("is_answered") is False]
        elif st_clean != "all":
            filtered = [r for r in filtered if r.get("status_norm", "").strip().lower() == st_clean]

    if gender:
        g_clean = gender.strip().lower()
        if g_clean != "all":
            filtered = [r for r in filtered if r.get("gender", "").strip().lower() == g_clean]

    if date_from:
        filtered = [r for r in filtered if r.get("calling_date") and r.get("calling_date") >= date_from]

    if date_to:
        filtered = [r for r in filtered if r.get("calling_date") and r.get("calling_date") <= date_to]

    if search:
        s_clean = search.strip().lower()
        filtered = [
            r for r in filtered if (
                s_clean in r.get("name", "").lower() or
                s_clean in r.get("customer_no", "").lower() or
                s_clean in r.get("poc", "").lower() or
                s_clean in r.get("district", "").lower() or
                s_clean in r.get("purpose", "").lower() or
                s_clean in r.get("remarks", "").lower()
            )
        ]

    return filtered

def recompute_analytics(filtered: List[dict]) -> dict:
    """Recompute KPIs and charts on filtered records."""
    total_calls = len(filtered)
    answered_calls = sum(1 for r in filtered if r.get("is_answered"))
    not_answered_calls = total_calls - answered_calls
    
    poc_counts = {}
    status_counts = {}
    gender_counts = {'Male': 0, 'Female': 0, 'Not Specified': 0}
    date_counts = {}
    district_counts = {}
    purpose_counts = {}
    membership_counts = {'Yes': 0, 'No': 0, 'Other': 0}
    donation_counts = {'Yes': 0, 'No': 0, 'Other': 0}

    for r in filtered:
        poc = r.get("poc", "").strip()
        is_ans = r.get("is_answered", False)
        g = r.get("gender", "Not Specified")
        d = r.get("calling_date", "")
        dist = r.get("district", "")
        purp = r.get("purpose", "")
        st = r.get("status_norm", "Other")
        mem = r.get("membership", "")
        don = r.get("donation_status", "")

        if poc:
            if poc not in poc_counts:
                poc_counts[poc] = {
                    'poc': poc, 'total': 0, 'answered': 0, 'not_answered': 0,
                    'male': 0, 'female': 0, 'membership_yes': 0, 'donation_yes': 0
                }
            poc_counts[poc]['total'] += 1
            if is_ans:
                poc_counts[poc]['answered'] += 1
            else:
                poc_counts[poc]['not_answered'] += 1
            if g == 'Male':
                poc_counts[poc]['male'] += 1
            elif g == 'Female':
                poc_counts[poc]['female'] += 1
            if mem == "Yes":
                poc_counts[poc]['membership_yes'] += 1
            if don == "Yes":
                poc_counts[poc]['donation_yes'] += 1

        status_counts[st] = status_counts.get(st, 0) + 1
        gender_counts[g] = gender_counts.get(g, 0) + 1

        if d:
            if d not in date_counts:
                date_counts[d] = {
                    'date': d,
                    'total': 0,
                    'answered': 0,
                    'not_answered': 0,
                    'male': 0,
                    'female': 0,
                    'pocs': set()
                }
            date_counts[d]['total'] += 1
            if is_ans:
                date_counts[d]['answered'] += 1
            else:
                date_counts[d]['not_answered'] += 1
            if g == 'Male':
                date_counts[d]['male'] += 1
            elif g == 'Female':
                date_counts[d]['female'] += 1
            if poc:
                date_counts[d]['pocs'].add(poc)

        if dist and dist.lower() not in ['na', 'none', 'null', '0', '-']:
            district_counts[dist] = district_counts.get(dist, 0) + 1

        if purp and purp.lower() not in ['na', 'none', 'null', '0', '-']:
            purpose_counts[purp] = purpose_counts.get(purp, 0) + 1

        if mem == "Yes":
            membership_counts['Yes'] += 1
        elif mem == "No":
            membership_counts['No'] += 1
        else:
            membership_counts['Other'] += 1

        if don == "Yes":
            donation_counts['Yes'] += 1
        elif don == "No":
            donation_counts['No'] += 1
        else:
            donation_counts['Other'] += 1

    poc_list = list(poc_counts.values())
    for p in poc_list:
        p['answer_rate'] = round((p['answered'] / p['total'] * 100), 1) if p['total'] > 0 else 0
    poc_list.sort(key=lambda x: x['total'], reverse=True)

    date_timeline = []
    for d_val, d_info in sorted(date_counts.items(), key=lambda x: x[0]):
        t = d_info['total']
        a = d_info['answered']
        rate = round((a / t * 100), 1) if t > 0 else 0
        date_timeline.append({
            'date': d_val,
            'total': t,
            'answered': a,
            'not_answered': d_info['not_answered'],
            'answer_rate': rate,
            'male': d_info['male'],
            'female': d_info['female'],
            'active_pocs': len(d_info['pocs'])
        })
    top_districts = sorted([{'district': k, 'count': v} for k, v in district_counts.items()], key=lambda x: x['count'], reverse=True)[:15]
    top_purposes = sorted([{'purpose': k, 'count': v} for k, v in purpose_counts.items()], key=lambda x: x['count'], reverse=True)[:10]

    answer_rate_pct = round((answered_calls / total_calls * 100), 1) if total_calls > 0 else 0
    drop_rate_pct = round((not_answered_calls / total_calls * 100), 1) if total_calls > 0 else 0

    return {
        'total_calls': total_calls,
        'answered_calls': answered_calls,
        'not_answered_calls': not_answered_calls,
        'answer_rate_pct': answer_rate_pct,
        'drop_rate_pct': drop_rate_pct,
        'poc_summary': poc_list,
        'status_breakdown': status_counts,
        'gender_breakdown': gender_counts,
        'date_timeline': date_timeline,
        'top_districts': top_districts,
        'top_purposes': top_purposes,
        'membership_summary': membership_counts,
        'donation_summary': donation_counts,
    }

@app.get("/api/analytics")
def get_analytics(
    sheet_id: str = "all",
    tab_name: Optional[str] = None,
    poc: Optional[str] = None,
    status: Optional[str] = None,
    gender: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None
):
    """Get analytics with active filters."""
    try:
        if sheet_id == "all":
            data = repository.get_combined_data()
        else:
            data = repository.get_sheet_data(sheet_id, tab_name)

        records = data.get("records", [])
        
        # Apply filters if any
        has_filter = any([poc, status, gender, date_from, date_to, search])
        if has_filter:
            filtered = filter_records(records, poc, status, gender, date_from, date_to, search)
            analytics = recompute_analytics(filtered)
            total_rows = len(filtered)
        else:
            analytics = data.get("analytics", {})
            total_rows = data.get("total_rows", 0)

        # Extract available POC list, status list, date bounds for dropdown filters
        all_pocs = sorted(list({r.get("poc") for r in records if r.get("poc")}))
        all_statuses = sorted(list({r.get("status_norm") for r in records if r.get("status_norm")}))
        all_dates = [r.get("calling_date") for r in records if r.get("calling_date")]
        min_date = min(all_dates) if all_dates else ""
        max_date = max(all_dates) if all_dates else ""

        return {
            "sheet_id": sheet_id,
            "tab_name": data.get("tab_name", ""),
            "total_rows": total_rows,
            "analytics": analytics,
            "filter_options": {
                "pocs": all_pocs,
                "statuses": all_statuses,
                "min_date": min_date,
                "max_date": max_date
            }
        }
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/records")
def get_records(
    sheet_id: str = "all",
    tab_name: Optional[str] = None,
    poc: Optional[str] = None,
    status: Optional[str] = None,
    gender: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    sort_by: str = "id",
    sort_order: str = "asc"
):
    """Get paginated calling records for the table."""
    try:
        if sheet_id == "all":
            data = repository.get_combined_data()
        else:
            data = repository.get_sheet_data(sheet_id, tab_name)

        records = data.get("records", [])
        filtered = filter_records(records, poc, status, gender, date_from, date_to, search)

        # Sorting
        reverse = (sort_order.lower() == "desc")
        try:
            filtered.sort(key=lambda x: (x.get(sort_by) is None, x.get(sort_by, "")), reverse=reverse)
        except:
            pass

        total_count = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        page_records = filtered[start:end]

        return {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size if total_count > 0 else 1,
            "records": page_records
        }
    except Exception as e:
        logger.error(f"Error fetching records: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export-csv")
def export_csv(
    sheet_id: str = "all",
    tab_name: Optional[str] = None,
    poc: Optional[str] = None,
    status: Optional[str] = None,
    gender: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None
):
    """Download filtered records as CSV."""
    if sheet_id == "all":
        data = repository.get_combined_data()
    else:
        data = repository.get_sheet_data(sheet_id, tab_name)

    records = data.get("records", [])
    filtered = filter_records(records, poc, status, gender, date_from, date_to, search)

    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [
        "SI No", "Date of Calling", "POC", "Customer No", "Name",
        "Calling Status", "Is Answered", "Gender", "Age", "District",
        "State", "Block", "Purpose of Calling", "Membership", "Donation Status", "Remarks"
    ]
    writer.writerow(headers)

    for r in filtered:
        writer.writerow([
            r.get("id", ""),
            r.get("calling_date", ""),
            r.get("poc", ""),
            r.get("customer_no", ""),
            r.get("name", ""),
            r.get("status", ""),
            "Yes" if r.get("is_answered") else "No",
            r.get("gender", ""),
            r.get("age", ""),
            r.get("district", ""),
            r.get("state", ""),
            r.get("block", ""),
            r.get("purpose", ""),
            r.get("membership", ""),
            r.get("donation_status", ""),
            r.get("remarks", "")
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=calling_data_{sheet_id}.csv"}
    )

# Mount static directory for frontend
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static_assets")
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
