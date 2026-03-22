"""
WRS Response Time & Call Volume Analysis
- By Day of Week
- By Time of Day (Night / Morning / Midday / Evening / Late)

Requirements:
    pip install pdfplumber pandas numpy

Usage:
    python wrs_analysis.py
    (update PDF_PATH below to point to your file)
"""

import pdfplumber
import re
import pandas as pd

# ── CONFIG ────────────────────────────────────────────────────────────────────
PDF_PATH      = r"C:\Users\vipon\Downloads\Ambulance\WRS_1.pdf"
OUTPUT_DETAIL = "wrs_response_times.csv"
OUTPUT_DOW    = "wrs_dow_summary.csv"
OUTPUT_VOLUME = "wrs_call_volume.csv"
OUTPUT_TOD    = "wrs_time_of_day.csv"
MAX_VALID_SEC = 3600
# ─────────────────────────────────────────────────────────────────────────────


def extract_lines(pdf_path: str) -> list:
    """Return every text line from every page of the PDF."""
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.extend(text.split("\n"))
    return lines


def parse_records(lines: list) -> pd.DataFrame:
    call_re  = re.compile(r"^(20\d{6}-\d{4})")
    time_re  = re.compile(r"\b(\d{2}:\d{2})\b")
    records  = []

    i = 0
    while i < len(lines):
        line = lines[i]
        m = call_re.match(line)
        if not m:
            i += 1
            continue

        call_num = m.group(1)
        date_str = f"{call_num[0:4]}-{call_num[4:6]}-{call_num[6:8]}"

        dispatch_time = None
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            if not call_re.match(next_line):
                times_found = time_re.findall(next_line)
                if times_found:
                    dispatch_time = times_found[0]

        after_dates = re.split(r"20\d{2}-\d{2}-\d{2}", line)
        last_part   = after_dates[-1].strip() if after_dates else ""
        nums = [
            int(n)
            for n in re.findall(r"-?\d+", last_part)
            if -999 < int(n) < 99_999
        ]

        d2e = nums[0] if len(nums) >= 1 else None
        e2o = nums[1] if len(nums) >= 2 else None
        d2o = nums[2] if len(nums) >= 3 else None
        o2a = nums[3] if len(nums) >= 4 else None

        records.append({
            "call_num":                 call_num,
            "date":                     date_str,
            "dispatch_time":            dispatch_time,
            "dispatch_to_enroute_sec":  d2e,
            "enroute_to_onscene_sec":   e2o,
            "dispatch_to_onscene_sec":  d2o,
            "onscene_to_available_sec": o2a,
        })
        i += 1

    df = pd.DataFrame(records)
    df["date"]        = pd.to_datetime(df["date"])
    df["day_of_week"] = df["date"].dt.day_name()
    df["dow_num"]     = df["date"].dt.dayofweek

    df["dispatch_dt"] = pd.to_datetime(
        df["date"].dt.strftime("%Y-%m-%d") + " " + df["dispatch_time"].fillna("00:00"),
        format="%Y-%m-%d %H:%M",
        errors="coerce",
    )
    df["hour"] = df["dispatch_dt"].dt.hour

    def assign_tod(hour):
        if pd.isna(hour):
            return None
        h = int(hour)
        if   h <  5: return "Night"
        elif h <  9: return "Morning"
        elif h < 13: return "Midday"
        elif h < 18: return "Evening"
        elif h < 22: return "Late"
        else:        return "Night"

    df["time_of_day"]             = df["hour"].apply(assign_tod)
    df["dispatch_to_onscene_min"] = df["dispatch_to_onscene_sec"] / 60
    df["enroute_to_onscene_min"]  = df["enroute_to_onscene_sec"]  / 60
    df["dispatch_to_enroute_min"] = df["dispatch_to_enroute_sec"] / 60
    return df


# ── RESPONSE TIME BY DAY OF WEEK ──────────────────────────────────────────────

def build_response_summary(df: pd.DataFrame):
    valid = df[
        df["dispatch_to_onscene_sec"].notna() &
        (df["dispatch_to_onscene_sec"] > 0) &
        (df["dispatch_to_onscene_sec"] < MAX_VALID_SEC)
    ].copy()

    valid_e2o = df[
        df["enroute_to_onscene_sec"].notna() &
        (df["enroute_to_onscene_sec"] > 0) &
        (df["enroute_to_onscene_sec"] < MAX_VALID_SEC)
    ].copy()
    valid_e2o["enroute_to_onscene_min"] = valid_e2o["enroute_to_onscene_sec"] / 60

    valid_d2e = df[
        df["dispatch_to_enroute_sec"].notna() &
        (df["dispatch_to_enroute_sec"] > 0) &
        (df["dispatch_to_enroute_sec"] < MAX_VALID_SEC)
    ].copy()
    valid_d2e["dispatch_to_enroute_min"] = valid_d2e["dispatch_to_enroute_sec"] / 60

    summary = (
        valid
        .groupby(["dow_num", "day_of_week"])["dispatch_to_onscene_min"]
        .agg(
            count        = "count",
            mean_min     = "mean",
            median_min   = "median",
            std_min      = "std",
            pct_under_8  = lambda x: (x < 8).mean()  * 100,
            pct_under_12 = lambda x: (x < 12).mean() * 100,
        )
        .reset_index()
        .sort_values("dow_num")
        .drop(columns="dow_num")
    )

    e2o_summary = (
        valid_e2o
        .groupby("day_of_week")["enroute_to_onscene_min"]
        .agg(
            e2o_mean_min   = "mean",
            e2o_median_min = "median",
        )
        .reset_index()
    )

    d2e_summary = (
        valid_d2e
        .groupby("day_of_week")["dispatch_to_enroute_min"]
        .agg(
            d2e_mean_min   = "mean",
            d2e_median_min = "median",
        )
        .reset_index()
    )

    summary = summary.merge(e2o_summary, on="day_of_week", how="left")
    summary = summary.merge(d2e_summary, on="day_of_week", how="left")

    return valid, valid_e2o, valid_d2e, summary


# ── CALL VOLUME BY DAY OF WEEK ────────────────────────────────────────────────

def build_volume_summary(df: pd.DataFrame) -> pd.DataFrame:
    daily_counts = (
        df.groupby("date")
        .agg(
            total_calls = ("call_num", "count"),
            day_of_week = ("day_of_week", "first"),
            dow_num     = ("dow_num", "first"),
        )
        .reset_index()
    )
    volume = (
        daily_counts
        .groupby(["dow_num", "day_of_week"])["total_calls"]
        .agg(
            days_observed = "count",
            avg_calls     = "mean",
            min_calls     = "min",
            max_calls     = "max",
            total_calls   = "sum",
        )
        .reset_index()
        .sort_values("dow_num")
        .drop(columns="dow_num")
    )
    return volume


# ── CALL VOLUME & RESPONSE TIME BY TIME OF DAY ───────────────────────────────

TOD_ORDER = ["Night", "Morning", "Midday", "Evening", "Late"]
TOD_HOURS = {
    "Night":   "00:00-04:59  &  22:00-23:59",
    "Morning": "05:00-08:59",
    "Midday":  "09:00-12:59",
    "Evening": "13:00-17:59",
    "Late":    "18:00-21:59",
}

def build_tod_summary(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df[df["time_of_day"].notna()].copy()

    vol = (
        df2.groupby("time_of_day")
        .agg(total_calls=("call_num", "count"))
        .reset_index()
    )

    valid = df2[
        df2["dispatch_to_onscene_sec"].notna() &
        (df2["dispatch_to_onscene_sec"] > 0) &
        (df2["dispatch_to_onscene_sec"] < MAX_VALID_SEC)
    ]
    resp = (
        valid.groupby("time_of_day")["dispatch_to_onscene_min"]
        .agg(
            resp_count   = "count",
            mean_min     = "mean",
            median_min   = "median",
            pct_under_8  = lambda x: (x < 8).mean()  * 100,
            pct_under_12 = lambda x: (x < 12).mean() * 100,
        )
        .reset_index()
    )

    valid_e2o = df2[
        df2["enroute_to_onscene_sec"].notna() &
        (df2["enroute_to_onscene_sec"] > 0) &
        (df2["enroute_to_onscene_sec"] < MAX_VALID_SEC)
    ].copy()
    valid_e2o["enroute_to_onscene_min"] = valid_e2o["enroute_to_onscene_sec"] / 60

    e2o = (
        valid_e2o.groupby("time_of_day")["enroute_to_onscene_min"]
        .agg(
            e2o_mean_min   = "mean",
            e2o_median_min = "median",
        )
        .reset_index()
    )

    valid_d2e = df2[
        df2["dispatch_to_enroute_sec"].notna() &
        (df2["dispatch_to_enroute_sec"] > 0) &
        (df2["dispatch_to_enroute_sec"] < MAX_VALID_SEC)
    ].copy()
    valid_d2e["dispatch_to_enroute_min"] = valid_d2e["dispatch_to_enroute_sec"] / 60

    d2e = (
        valid_d2e.groupby("time_of_day")["dispatch_to_enroute_min"]
        .agg(
            d2e_mean_min   = "mean",
            d2e_median_min = "median",
        )
        .reset_index()
    )

    tod = vol.merge(resp, on="time_of_day", how="left")
    tod = tod.merge(e2o,  on="time_of_day", how="left")
    tod = tod.merge(d2e,  on="time_of_day", how="left")
    tod["hours"]     = tod["time_of_day"].map(TOD_HOURS)
    tod["tod_order"] = tod["time_of_day"].map(
        {v: i for i, v in enumerate(TOD_ORDER)}
    )
    tod = tod.sort_values("tod_order").drop(columns="tod_order")
    return tod


# ── PRINT HELPERS ─────────────────────────────────────────────────────────────

def print_response_summary(summary: pd.DataFrame, valid: pd.DataFrame,
                            valid_e2o: pd.DataFrame, valid_d2e: pd.DataFrame) -> None:
    pd.set_option("display.float_format", "{:.1f}".format)
    print("\n" + "=" * 75)
    print("  Response Time (Dispatch -> On-Scene)  ---  by Day of Week")
    print("=" * 75)
    print(summary.to_string(index=False))
    print("-" * 75)
    print(f"  Overall dispatch->onscene mean   : {valid['dispatch_to_onscene_min'].mean():.1f} min")
    print(f"  Overall dispatch->onscene median : {valid['dispatch_to_onscene_min'].median():.1f} min")
    print(f"  Overall dispatch->enroute mean   : {valid_d2e['dispatch_to_enroute_min'].mean():.1f} min")
    print(f"  Overall dispatch->enroute median : {valid_d2e['dispatch_to_enroute_min'].median():.1f} min")
    print(f"  Overall enroute->onscene mean    : {valid_e2o['enroute_to_onscene_min'].mean():.1f} min")
    print(f"  Overall enroute->onscene median  : {valid_e2o['enroute_to_onscene_min'].median():.1f} min")
    print(f"  % under  8 min                   : {(valid['dispatch_to_onscene_min'] < 8).mean()*100:.1f}%")
    print(f"  % under 12 min                   : {(valid['dispatch_to_onscene_min'] < 12).mean()*100:.1f}%")
    print(f"  Valid records                    : {len(valid)}")
    print("=" * 75 + "\n")


def print_volume(volume: pd.DataFrame) -> None:
    pd.set_option("display.float_format", "{:.1f}".format)
    print("\n" + "=" * 65)
    print("  Call Volume  ---  Average Calls per Day of Week")
    print("=" * 65)
    print(volume.to_string(index=False))
    print("-" * 65)
    print(f"  Busiest day  : {volume.loc[volume['avg_calls'].idxmax(), 'day_of_week']}")
    print(f"  Quietest day : {volume.loc[volume['avg_calls'].idxmin(), 'day_of_week']}")
    print("=" * 65 + "\n")


def print_tod(tod: pd.DataFrame) -> None:
    pd.set_option("display.float_format", "{:.1f}".format)
    print("\n" + "=" * 90)
    print("  Call Volume & Response Time  ---  by Time of Day")
    print("=" * 90)
    print(tod.to_string(index=False))
    print("-" * 90)
    print(f"  Most calls   : {tod.loc[tod['total_calls'].idxmax(), 'time_of_day']}")
    print(f"  Fewest calls : {tod.loc[tod['total_calls'].idxmin(), 'time_of_day']}")
    print(f"  Fastest resp : {tod.loc[tod['mean_min'].idxmin(),    'time_of_day']}")
    print(f"  Slowest resp : {tod.loc[tod['mean_min'].idxmax(),    'time_of_day']}")
    print("=" * 90 + "\n")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Reading {PDF_PATH} ...")
    lines = extract_lines(PDF_PATH)
    print(f"  {len(lines):,} text lines extracted")

    df = parse_records(lines)
    print(f"  {len(df):,} call records parsed")

    parsed_times = df["dispatch_time"].notna().sum()
    print(f"  {parsed_times:,} records with dispatch time parsed")
    print(f"  Hour distribution sample:\n{df['time_of_day'].value_counts().to_string()}\n")

    valid, valid_e2o, valid_d2e, response_summary = build_response_summary(df)
    print_response_summary(response_summary, valid, valid_e2o, valid_d2e)

    volume = build_volume_summary(df)
    print_volume(volume)

    tod = build_tod_summary(df)
    print_tod(tod)

    df.to_csv(OUTPUT_DETAIL,            index=False)
    response_summary.to_csv(OUTPUT_DOW, index=False)
    volume.to_csv(OUTPUT_VOLUME,        index=False)
    tod.to_csv(OUTPUT_TOD,              index=False)
    print(f"Saved: {OUTPUT_DETAIL}, {OUTPUT_DOW}, {OUTPUT_VOLUME}, {OUTPUT_TOD}")


if __name__ == "__main__":
    main()