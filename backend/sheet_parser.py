import re
from datetime import datetime, timedelta
import openpyxl

MONTH_NAMES = [
    'january', 'jan', 'february', 'feb', 'march', 'mar', 'april', 'apr',
    'may', 'june', 'jun', 'july', 'jul', 'august', 'aug', 'september',
    'sept', 'sep', 'october', 'oct', 'november', 'nov', 'december', 'dec'
]

COLUMN_ALIASES = {
    'poc': ['poc', 'caller', 'agent', 'calling poc', 'caller name'],
    'calling_date': ['date of calling', 'calling date', 'call date', 'calling_date', 'date of schedule'],
    'incoming_date': ['date of incoming', 'incoming date', 'date of incomming'],
    'status': ['calling status', 'call status', 'status of calling', 'status', 'calling status report'],
    'customer_no': ['customerno', 'customer no', 'number', 'phone', 'mobile', 'contact no', 'contact number'],
    'whatsapp_no': ['whatsapp no', 'whatsapp', 'wa no', 'whatsapp number'],
    'name': ['name', 'customer name', 'client name', 'person name'],
    'gender': ['gender', 'sex', 'm/f'],
    'age': ['age'],
    'state': ['state'],
    'district': ['district', 'dist'],
    'block': ['block'],
    'panchayat': ['panchayat'],
    'village': ['village'],
    'pin_code': ['pin code', 'pincode', 'pin'],
    'purpose': ['purpose of calling', 'purpose', 'purpose of meeting'],
    'membership': ['membership', 'membership status', 'member'],
    'donation_status': ['donation status', 'donation_status'],
    'donation': ['donation', 'donation amount', 'amount', 'contribution'],
    'onboarding_status': ['onboarding status', 'onboarding'],
    'remarks': ['remark', 'remarks', 'details', 'purpose remakrs', 'purpose remarks', 'note', 'notes', 'comment']
}

def extract_sheet_id(url_or_id: str) -> str:
    """Extract Google Sheet ID from URL or return if already an ID."""
    url_or_id = url_or_id.strip()
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url_or_id)
    if match:
        return match.group(1)
    # Check if raw ID
    if re.match(r'^[a-zA-Z0-9-_]{20,}$', url_or_id):
        return url_or_id
    return url_or_id

def detect_tab_type(sheet_name: str):
    """Categorize and score a tab name to determine if it's the active working month sheet."""
    name_clean = sheet_name.strip()
    name_lower = name_clean.lower()
    
    month_pattern = r'(' + '|'.join(MONTH_NAMES) + r')'
    # Month followed by Year (e.g. September 2026, Jan, 2026, Sep-26)
    m_a = re.search(rf'{month_pattern}[\s,_\-\.]*(\d{{4}}|\d{{2}})', name_lower)
    # Year followed by Month (e.g. 2026 September, 2026-Jan)
    m_b = re.search(rf'(\d{{4}})[\s,_\-\.]*{month_pattern}', name_lower)
    # Numeric Month-Year (e.g. 09-2026, 2026-09)
    m_c = re.search(r'(0[1-9]|1[0-2])[\s,_\-\.](20\d\d)', name_lower) or re.search(r'(20\d\d)[\s,_\-\.](0[1-9]|1[0-2])', name_lower)

    if m_a or m_b or m_c:
        return 'monthly_calling', 10, "Monthly Calling Sheet (Working Data)"

    # Compile / Donation / Membership tab
    if any(k in name_lower for k in ['compile', 'compiled', 'donation', 'membership', 'master', 'consolidat']):
        return 'compile_records', 8, "Compile / Donation / Membership Record"

    # Report / Summary tab
    if any(k in name_lower for k in ['report', 'summary', 'format', 'validation', 'retro']):
        return 'report_summary', 3, "Report / Summary Sheet"

    return 'other', 1, "Other Sheet"

def parse_date_value(val) -> str:
    """Parse Excel serial date, datetime, or date string into YYYY-MM-DD."""
    if not val:
        return ""
    if isinstance(val, datetime):
        return val.strftime('%Y-%m-%d')
    if isinstance(val, (int, float)):
        try:
            # Excel base date 1899-12-30
            if 30000 <= val <= 60000:
                dt = datetime(1899, 12, 30) + timedelta(days=float(val))
                return dt.strftime('%Y-%m-%d')
        except:
            pass
        return str(int(val)) if isinstance(val, float) and val.is_integer() else str(val)
    
    val_str = str(val).strip()
    # Check YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}', val_str):
        return val_str[:10]
    # Check DD/MM/YYYY or DD-MM-YYYY
    m = re.match(r'^(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', val_str)
    if m:
        d, mth, y = m.groups()
        return f"{y}-{int(mth):02d}-{int(d):02d}"
    return val_str

def parse_phone_value(val) -> str:
    """Format phone numbers cleanly without float scientific notation."""
    if not val:
        return ""
    if isinstance(val, (int, float)):
        try:
            return str(int(val))
        except:
            return str(val)
    s = str(val).strip()
    if s.endswith('.0'):
        s = s[:-2]
    return s

def normalize_status(val: str):
    """Normalize call status and return (normalized_category, is_answered)."""
    if not val:
        return 'Not Recorded', False
    s = str(val).strip()
    s_low = s.lower()
    
    if s_low == 'answered':
        return 'Answered', True
    elif 'not answered' in s_low or 'unanswered' in s_low:
        return 'Not Answered', False
    elif 'busy' in s_low:
        return 'Busy', False
    elif 'switch off' in s_low or 'switched off' in s_low:
        return 'Switch Off', False
    elif 'out of network' in s_low or 'network' in s_low:
        return 'Out of Network', False
    elif 'incoming off' in s_low or 'incomming off' in s_low:
        return 'Incoming Off', False
    elif any(k in s_low for k in ['invalid', 'wrong number', 'wrong no', 'duplicate']):
        return 'Invalid / Wrong No.', False
    elif 'call back' in s_low or 'callback' in s_low:
        return 'Call Back Requested', False
    else:
        return s.title(), False

def normalize_gender(val: str) -> str:
    """Normalize gender strings to Male, Female, or Not Specified."""
    if not val:
        return 'Not Specified'
    g = str(val).strip().lower()
    if g in ['male', 'm', 'purush']:
        return 'Male'
    elif g in ['female', 'f', 'mahila', 'stri']:
        return 'Female'
    return 'Not Specified'

def map_headers(header_row):
    """Match sheet columns with alias keys."""
    col_map = {}
    clean_headers = [str(h).strip().lower() if h is not None else "" for h in header_row]

    # Exact matches first
    for field, aliases in COLUMN_ALIASES.items():
        for i, h in enumerate(clean_headers):
            if not h: continue
            if h in aliases:
                col_map[field] = i
                break
    
    # Substring matches for unmapped fields
    for field, aliases in COLUMN_ALIASES.items():
        if field in col_map:
            continue
        for i, h in enumerate(clean_headers):
            if not h or i in col_map.values():
                continue
            for a in aliases:
                if len(a) > 3 and a in h:
                    col_map[field] = i
                    break
            if field in col_map:
                break

    return col_map

def inspect_workbook(xlsx_path: str):
    """List tabs in workbook with detection classification and scoring."""
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    tabs_info = []
    
    for s_name in wb.sheetnames:
        tab_type, score, desc = detect_tab_type(s_name)
        tabs_info.append({
            "name": s_name,
            "type": tab_type,
            "score": score,
            "description": desc
        })
    
    # Sort highest score first
    tabs_info.sort(key=lambda x: x["score"], reverse=True)
    recommended = tabs_info[0]["name"] if tabs_info else ""
    return tabs_info, recommended

def parse_sheet_tab(xlsx_path: str, tab_name: str, max_records_for_ui: int = 50000):
    """Parse a specific sheet tab with high performance and calculate analytics."""
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    if tab_name not in wb.sheetnames:
        # Fallback to recommended or first
        tab_name = wb.sheetnames[0]
        
    ws = wb[tab_name]
    row_iter = ws.iter_rows(values_only=True)
    try:
        header_row = next(row_iter)
    except StopIteration:
        return {"records": [], "analytics": {}, "total_rows": 0}
        
    col_map = map_headers(header_row)
    
    records = []
    poc_counts = {}
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

    idx = 0
    for row in row_iter:
        if not any(row):
            continue
            
        def get_val(field):
            col = col_map.get(field)
            if col is not None and col < len(row):
                return row[col]
            return None

        poc = str(get_val('poc')).strip() if get_val('poc') is not None else ""
        raw_status = get_val('status')
        raw_date = get_val('calling_date')
        cust_no = parse_phone_value(get_val('customer_no'))
        
        # Skip completely empty filler rows
        if not poc and not raw_status and not cust_no and not raw_date:
            continue

        idx += 1
        call_date = parse_date_value(raw_date)
        status_norm, is_ans = normalize_status(raw_status)
        gender_norm = normalize_gender(get_val('gender'))
        name = str(get_val('name')).strip() if get_val('name') is not None else ""
        district = str(get_val('district')).strip().title() if get_val('district') is not None else ""
        purpose = str(get_val('purpose')).strip() if get_val('purpose') is not None else ""
        
        raw_mem = str(get_val('membership')).strip().lower() if get_val('membership') is not None else ""
        raw_don = str(get_val('donation_status')).strip().lower() if get_val('donation_status') is not None else ""
        
        mem_status = "Yes" if "yes" in raw_mem else ("No" if "no" in raw_mem else ("Not Specified" if not raw_mem else raw_mem.title()))
        don_status = "Yes" if "yes" in raw_don else ("No" if "no" in raw_don else ("Not Specified" if not raw_don else raw_don.title()))
        
        # Accumulate metrics
        total_calls += 1
        if is_ans:
            answered_calls += 1
        else:
            not_answered_calls += 1
            
        # POC stats
        if poc:
            if poc not in poc_counts:
                poc_counts[poc] = {
                    'poc': poc,
                    'total': 0,
                    'answered': 0,
                    'not_answered': 0,
                    'male': 0,
                    'female': 0,
                    'membership_yes': 0,
                    'donation_yes': 0
                }
            poc_counts[poc]['total'] += 1
            if is_ans:
                poc_counts[poc]['answered'] += 1
            else:
                poc_counts[poc]['not_answered'] += 1
            if gender_norm == 'Male':
                poc_counts[poc]['male'] += 1
            elif gender_norm == 'Female':
                poc_counts[poc]['female'] += 1
            if mem_status == "Yes":
                poc_counts[poc]['membership_yes'] += 1
            if don_status == "Yes":
                poc_counts[poc]['donation_yes'] += 1

        # Status counts
        status_counts[status_norm] = status_counts.get(status_norm, 0) + 1
        
        # Gender counts
        gender_counts[gender_norm] = gender_counts.get(gender_norm, 0) + 1
        
        # Date counts
        if call_date and re.match(r'^\d{4}-\d{2}-\d{2}$', call_date):
            if call_date not in date_counts:
                date_counts[call_date] = {'date': call_date, 'total': 0, 'answered': 0, 'not_answered': 0}
            date_counts[call_date]['total'] += 1
            if is_ans:
                date_counts[call_date]['answered'] += 1
            else:
                date_counts[call_date]['not_answered'] += 1

        # District counts
        if district and district.lower() not in ['na', 'none', 'null', '0', '-']:
            district_counts[district] = district_counts.get(district, 0) + 1

        # Purpose counts
        if purpose and purpose.lower() not in ['na', 'none', 'null', '0', '-']:
            purpose_counts[purpose] = purpose_counts.get(purpose, 0) + 1

        # Membership / Donation counts
        if mem_status == "Yes":
            membership_counts['Yes'] += 1
        elif mem_status == "No":
            membership_counts['No'] += 1
        else:
            membership_counts['Other'] += 1

        if don_status == "Yes":
            donation_counts['Yes'] += 1
        elif don_status == "No":
            donation_counts['No'] += 1
        else:
            donation_counts['Other'] += 1

        # Store record for table
        if len(records) < max_records_for_ui:
            record_obj = {
                'id': idx,
                'poc': poc,
                'calling_date': call_date,
                'status': str(raw_status or '').strip(),
                'status_norm': status_norm,
                'is_answered': is_ans,
                'customer_no': cust_no,
                'name': name,
                'gender': gender_norm,
                'age': str(get_val('age') or '').strip().replace('.0', ''),
                'state': str(get_val('state') or '').strip(),
                'district': district,
                'block': str(get_val('block') or '').strip(),
                'panchayat': str(get_val('panchayat') or '').strip(),
                'village': str(get_val('village') or '').strip(),
                'purpose': purpose,
                'membership': mem_status,
                'donation_status': don_status,
                'donation': str(get_val('donation') or '').strip(),
                'remarks': str(get_val('remarks') or '').strip()
            }
            records.append(record_obj)

    # Calculate answer rate % for each POC
    poc_list = list(poc_counts.values())
    for p in poc_list:
        p['answer_rate'] = round((p['answered'] / p['total'] * 100), 1) if p['total'] > 0 else 0
    poc_list.sort(key=lambda x: x['total'], reverse=True)

    # Sort dates chronologically
    date_timeline = sorted(list(date_counts.values()), key=lambda x: x['date'])

    # District top 15
    top_districts = sorted([{'district': k, 'count': v} for k, v in district_counts.items()], key=lambda x: x['count'], reverse=True)[:15]

    # Purpose top 10
    top_purposes = sorted([{'purpose': k, 'count': v} for k, v in purpose_counts.items()], key=lambda x: x['count'], reverse=True)[:10]

    answer_rate_pct = round((answered_calls / total_calls * 100), 1) if total_calls > 0 else 0
    drop_rate_pct = round((not_answered_calls / total_calls * 100), 1) if total_calls > 0 else 0

    analytics = {
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

    return {
        'tab_name': tab_name,
        'total_rows': total_calls,
        'analytics': analytics,
        'records': records
    }

