# reports/views.py
from datetime import timedelta
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from inventory.models import Medicine, Transaction

# ---- field names ----
TXN_DATE_FIELD   = "created_at"
TXN_TYPE_FIELD   = "ttype"
QTY_FIELD        = "quantity"
PRICE_FIELD      = "unit_price"
MEDICINE_FK      = "medicine"
EXPIRY_FIELD     = "exp_date"
COST_FIELD       = "cost_price"
ON_HAND_FIELD    = "quantity_on_hand"

@login_required
def reports_view(request):
    user = request.user
    today = timezone.localdate()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    # ========= TRANSACTIONS =========
    txns_qs = (
        Transaction.objects
        .filter(owner=user)
        .select_related(MEDICINE_FK)
        .values(TXN_DATE_FIELD, TXN_TYPE_FIELD, QTY_FIELD, PRICE_FIELD, f"{MEDICINE_FK}__name", "partner_name")
    )
    txns = list(txns_qs)
    df = pd.DataFrame(txns)

    if not df.empty:
        df[TXN_DATE_FIELD] = pd.to_datetime(df[TXN_DATE_FIELD])
        df["date_only"] = df[TXN_DATE_FIELD].dt.date
        df["type_u"] = df[TXN_TYPE_FIELD].astype(str).str.upper()
        df["is_sold"] = df["type_u"].isin(["SOLD", "EXPORT"])
        df["is_bought"] = df["type_u"].isin(["BOUGHT", "IMPORT"])
        df["amount"] = df[QTY_FIELD].fillna(0).astype(float) * df[PRICE_FIELD].fillna(0).astype(float)
        df["med_name"] = df[f"{MEDICINE_FK}__name"].fillna("—")
        df["partner_name"] = df["partner_name"].fillna("-")

    # ========= SUMMARY CARDS =========
    rev_day = rev_week = rev_month = rev_year = 0.0
    if not df.empty:
        day_mask = df["date_only"].eq(today)
        week_mask = df["date_only"].between(start_of_week, today)
        month_mask = df["date_only"].between(start_of_month, today)
        year_mask = df[TXN_DATE_FIELD].dt.year.eq(today.year)
        sold_mask = df["is_sold"]

        rev_day   = float(df.loc[sold_mask & day_mask, "amount"].sum())
        rev_week  = float(df.loc[sold_mask & week_mask, "amount"].sum())
        rev_month = float(df.loc[sold_mask & month_mask, "amount"].sum())
        rev_year  = float(df.loc[sold_mask & year_mask, "amount"].sum())

    # ========= REVENUE TIMESERIES =========
    days_back = 60
    start_ts = today - timedelta(days=days_back - 1)
    ts_dates = pd.date_range(start_ts, periods=days_back, freq="D").date
    ts_series = pd.Series(0.0, index=pd.Index(ts_dates, name="date_only"))
    if not df.empty:
        rev_by_day = df.loc[df["is_sold"]].groupby("date_only")["amount"].sum()
        ts_series = ts_series.add(rev_by_day, fill_value=0.0)
    revenue_timeseries = [{"date": d.isoformat(), "revenue": float(v)} for d, v in ts_series.items()]

    # ========= TOP MEDICINES =========
    top_medicines = []
    if not df.empty:
        g = df.loc[df["is_sold"]].groupby("med_name")[QTY_FIELD].sum().sort_values(ascending=False).head(10)
        top_medicines = [{"name": n, "qty_sold": int(q)} for n, q in g.items()]

    # ========= EXPIRY PIE =========
    meds_qs = Medicine.objects.filter(owner=user).values("name", EXPIRY_FIELD, ON_HAND_FIELD, COST_FIELD)
    df_meds = pd.DataFrame(list(meds_qs))
    expired = expiring_30d = ok = 0
    if not df_meds.empty:
        df_meds[EXPIRY_FIELD] = pd.to_datetime(df_meds[EXPIRY_FIELD]).dt.date
        expired = int((df_meds[EXPIRY_FIELD] < today).sum())
        expiring_30d = int(((df_meds[EXPIRY_FIELD] >= today) & (df_meds[EXPIRY_FIELD] <= today + timedelta(days=30))).sum())
        ok = int((df_meds[EXPIRY_FIELD] > today + timedelta(days=30)).sum())
    expiry_pie = {"expired": expired, "expiring_30d": expiring_30d, "ok": ok}

    # ========= WEEKLY BOUGHT/SOLD =========
    weekly_bought_sold = []
    if not df.empty:
        iso = df[TXN_DATE_FIELD].dt.isocalendar()
        df["week_key"] = iso["year"].astype(str) + "-W" + iso["week"].astype(str).str.zfill(2)
        g_b = df.loc[df["is_bought"]].groupby("week_key")[QTY_FIELD].sum()
        g_s = df.loc[df["is_sold"]].groupby("week_key")[QTY_FIELD].sum()
        all_weeks = sorted(set(g_b.index).union(set(g_s.index)))
        for wk in all_weeks:
            weekly_bought_sold.append({
                "week": wk, "bought": int(g_b.get(wk, 0)), "sold": int(g_s.get(wk, 0))
            })

    # ========= RECENT TRANSACTIONS =========
    recent_qs = (
        Transaction.objects.filter(owner=user)
        .select_related(MEDICINE_FK)
        .order_by(f"-{TXN_DATE_FIELD}")[:15]
    )
    recent_transactions = []
    for t in recent_qs:
        dtv = getattr(t, TXN_DATE_FIELD, None)
        if hasattr(dtv, "date"):
            dtv = dtv.date()
        med = getattr(t, MEDICINE_FK, None)
        partner = getattr(t, "partner_name", None) or getattr(t, "partner", "-")
        qty = int(getattr(t, QTY_FIELD, 0) or 0)
        unit_price = float(getattr(t, PRICE_FIELD, 0.0) or 0.0)
        recent_transactions.append({
            "date": dtv.isoformat() if dtv else "-",
            "type": getattr(t, TXN_TYPE_FIELD, "-"),
            "partner": partner,
            "medicine": getattr(med, "name", "-") if med else "-",
            "unit_price": unit_price,
            "qty": qty,
            "total": float(qty * unit_price),
        })

    # ========= PROFIT SUMMARY TABLE =========
    detailed_rows = []
    if not df_meds.empty:
        df_meds["on_hand"] = df_meds[ON_HAND_FIELD].fillna(0).astype(int)
        df_meds["cost"] = df_meds[COST_FIELD].fillna(0.0).astype(float)
        sold_qty = df.loc[df["is_sold"]].groupby("med_name")[QTY_FIELD].sum() if not df.empty else pd.Series(dtype=float)
        revenue = df.loc[df["is_sold"]].groupby("med_name")["amount"].sum() if not df.empty else pd.Series(dtype=float)
        bought_qty = df.loc[df["is_bought"]].groupby("med_name")[QTY_FIELD].sum() if not df.empty else pd.Series(dtype=float)
        meds_names = df_meds["name"].tolist()
        s_bought = bought_qty.reindex(meds_names).fillna(0).astype(int)
        s_sold = sold_qty.reindex(meds_names).fillna(0).astype(int)
        s_rev = revenue.reindex(meds_names).fillna(0.0).astype(float)

        for _, row in df_meds.iterrows():
            name = row["name"]
            bought = int(s_bought.get(name, 0))
            sold = int(s_sold.get(name, 0))
            rem = int(row["on_hand"])
            cost = float(row["cost"])
            rev = float(s_rev.get(name, 0.0))
            cogs = float(sold * cost)
            expired_loss = float(rem * cost) if (row[EXPIRY_FIELD] < today) else 0.0
            profit = float(rev - cogs - expired_loss)
            profit_pct = float((profit / rev) * 100.0) if rev else 0.0
            detailed_rows.append({
                "medicine": name, "bought": bought, "sold": sold, "remaining": rem,
                "revenue": rev, "cogs": cogs, "expired_loss": expired_loss,
                "profit": profit, "profit_pct": profit_pct
            })

    total_profit = sum(r["profit"] for r in detailed_rows)
    expired_loss_total = sum(r["expired_loss"] for r in detailed_rows)
    total_revenue = sum(r["revenue"] for r in detailed_rows)
    profit_pct_overall = (total_profit / total_revenue * 100.0) if total_revenue else None

    inv_by_medicine = [{"name": r["medicine"], "remaining": r["remaining"]} for r in detailed_rows]
    profit_by_medicine = [{"name": r["medicine"], "profit": r["profit"]} for r in detailed_rows]

    # ========= FULL DATA FOR EXCEL =========
    all_transactions = list(
        Transaction.objects.filter(owner=user)
        .select_related(MEDICINE_FK)
        .values("created_at", "ttype", "partner_name", "medicine__name", "unit_price", "quantity")
    )
    all_detailed_rows = detailed_rows

    context = {
        "rev_day": rev_day, "rev_week": rev_week, "rev_month": rev_month, "rev_year": rev_year,
        "total_profit": total_profit, "expired_loss_total": expired_loss_total,
        "profit_pct_overall": profit_pct_overall,
        "recent_transactions": recent_transactions, "detailed_rows": detailed_rows,
        "revenue_timeseries": revenue_timeseries, "top_medicines": top_medicines,
        "expiry_pie": expiry_pie, "weekly_bought_sold": weekly_bought_sold,
        "inv_by_medicine": inv_by_medicine, "profit_by_medicine": profit_by_medicine,
        "all_transactions": list(all_transactions),
        "all_detailed_rows": all_detailed_rows,
    }
    return render(request, "reports/reports.html", context)
