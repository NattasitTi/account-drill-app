import streamlit as st
import pandas as pd
from databricks import sql as dbsql
import os
import io

# ── Config ─────────────────────────────────────────────────────────────────
TABLE = "risk_dev.dev_stg_dbcube.tb_all_cube_test_v1"

# Dimensions ทั้งหมด (ล้อตาม metric view)
DIMENSIONS = [
    "data_month","data_year","data_yearqq","datamonth_qq",
    "book_month","book_year","book_yearqq","bookmonth_qq",
    "product","subproduct","product_snap","subproduct_snap",
    "bucket","behavior_grade","segment","segment_risk_level",
    "region","region_ori","location_province","location_region",
    "branch_name_thai","branch_abbr","branch_area","area",
    "ncb_grade","ncb_group","ncb_grade_retro","ncb_grade_ori",
    "ncb_grade_review","ncb_grade_review_202503","ncb_grade_review_202506",
    "ncb_grade_review_202509","ncb_grade_review_202512","ncb_grade_review_202603",
    "band_ascore","band_ascore_car","band_ascore_mcloan",
    "final_band_retro","final_band_retro_mcloan","combine_score_band",
    "sex","range_cust_age","occupation_desc_group_new",
    "business_type_desc_new","channel","customer_type_desc",
    "g_tenor_range","tenor_range","fin_range","ltv_range",
    "loantype_desc","iir_range","installment_range",
    "flag_bad_good","flag_newcust","check_new_account",
    "mob","flag_test","test_production","flag_purge",
    "ever_debtre","ever_yfwh","flag_early_wo",
    "flag_color_final","flag_war_final","eligible_flood",
    "type_debtre","type_covid",
    "last3m_mob3","last6m_mob6","last9m_mob9","last12m_mob12",
    "f_bhv3m","f_bhv6m","f_bhv12m",
    "dim_name","mob_loss",
    "agreement_no","account_key",
]

# Measures (additive SUM ล้อตาม metric view)
MEASURES = {
    "total_port":           "Total Port (NEA)",
    "total_port_acct":      "Total Port Accounts",
    "nea":                  "NEA",
    "amt_30plus":           "30+ Amount",
    "cnt_30plus":           "30+ Accounts",
    "amt_60plus":           "60+ Amount",
    "cnt_60plus":           "60+ Accounts",
    "amt_90plus":           "90+ Amount",
    "cnt_90plus":           "90+ Accounts",
    "x":                    "X DPD Amount",
    "x_acct":               "X DPD Accounts",
    "write_off":            "Write Off",
    "write_off_acct":       "Write Off Accounts",
    "ecl_total":            "ECL Total",
    "ecl_normal":           "ECL Normal",
    "gca":                  "GCA",
    "fin_newbook":          "New Booking Amount",
    "fin_newbook_acct":     "New Booking Accounts",
    "amt_30plus_mob3":      "30+ MOB3 Amount",
    "cnt_30plus_mob3":      "30+ MOB3 Accounts",
    "amt_30plus_mob6":      "30+ MOB6 Amount",
    "cnt_30plus_mob6":      "30+ MOB6 Accounts",
    "amt_60plus_mob6":      "60+ MOB6 Amount",
    "cnt_60plus_mob6":      "60+ MOB6 Accounts",
    "amt_90plus_mob6":      "90+ MOB6 Amount",
    "cnt_90plus_mob6":      "90+ MOB6 Accounts",
    "xplus_mob2":           "X+ MOB2 Amount",
    "xplus_mob2_acct":      "X+ MOB2 Accounts",
    "fpd1":                 "FPD1",
    "fpd2":                 "FPD2",
    "fpd3":                 "FPD3",
    "fpd4":                 "FPD4",
    "total_fmob_acct":      "Total FMOB Accounts",
    "recovery_los":         "Recovery LOS",
    "recovery_repo":        "Recovery Repo",
    "recovery_payment":     "Recovery Payment",
    "loss":                 "Loss",
    "loss_risk":            "Loss Risk",
    "worepo_amt":           "WO+Repo Amount",
    "worepo_fair":          "WO+Repo Fair",
    "provision_los":        "Provision LOS",
    "ead_amount":           "EAD Amount",
    "lgd_amount":           "LGD Amount",
    "total_account":        "Total Account",
    "total_account_pay":    "Total Account Pay",
    "wo_los":               "WO LOS",
    "collateral_value":     "Collateral Value",
}

# Measures ที่ต้อง compute (ratio) — แสดงใน summary เป็น derived
RATIO_MEASURES = {
    "%30+":      ("amt_30plus",      "total_port"),
    "%60+":      ("amt_60plus",      "total_port"),
    "%90+":      ("amt_90plus",      "total_port"),
    "%30+mob3":  ("amt_30plus_mob3", "fin_newbook"),
    "%30+mob6":  ("amt_30plus_mob6", "fin_newbook"),
    "%60+mob6":  ("amt_60plus_mob6", "fin_newbook"),
    "%90+mob6":  ("amt_90plus_mob6", "fin_newbook"),
}

# Columns แสดงในตาราง (default)
DEFAULT_DISPLAY_COLS = [
    "agreement_no","data_month","product","subproduct","bucket",
    "ncb_grade","region","branch_name_thai","behavior_grade","mob",
    "total_port","nea","amt_30plus","amt_90plus","write_off",
]

# ── Databricks connection ───────────────────────────────────────────────────
@st.cache_resource
def get_connection():
    return dbsql.connect(
        server_hostname = os.environ["DATABRICKS_HOST"],
        http_path       = os.environ["DATABRICKS_HTTP_PATH"],
        access_token    = os.environ["DATABRICKS_TOKEN"],
    )

def run_query(sql: str) -> pd.DataFrame:
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql)
    return cursor.fetchall_arrow().to_pandas()

@st.cache_data(ttl=3600)
def get_distinct_values(col: str) -> list:
    """ดึงค่า distinct ของ column สำหรับ dropdown (cache 1 ชม.)"""
    df = run_query(f"""
        select distinct {col}
        from {TABLE}
        where data_month >= 202601
          and {col} is not null
        order by {col}
        limit 500
    """)
    return df.iloc[:, 0].tolist()

# ── UI ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "Account Drill — Tidlor Risk Portfolio",
    page_icon  = "🔍",
    layout     = "wide",
)

st.title("🔍 Account Drill")
st.caption("ค้นหารายบัญชีแบบ Dynamic Filter | Risk Portfolio Analytics")

# ── Sidebar: Filter ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Filter")
    st.caption("เลือก Dimension ที่ต้องการ filter")

    # data_month — บังคับ (text input ไม่ใช่ dropdown เพราะค่าเยอะ)
    data_month_input = st.text_input(
        "data_month * (บังคับ)", value="202607",
        help="format YYYYMM เช่น 202607 | ใส่หลายเดือนคั่นด้วยจุลภาค เช่น 202606,202607"
    )

    st.divider()
    st.subheader("Dimensions (optional)")
    st.caption("เลือก dimension ที่อยากกรอง แล้วเลือกค่า")

    # Dynamic: user เลือก dimension ที่อยากกรองก่อน
    selected_dims = st.multiselect(
        "เลือก Dimension ที่ต้องการ filter",
        options=[d for d in DIMENSIONS if d not in ("data_month","agreement_no","account_key")],
        default=["product","bucket"],
        help="เลือกได้หลาย dimension"
    )

    # แสดง widget ตาม dimension ที่เลือก
    dim_filters = {}
    for dim in selected_dims:
        with st.expander(f"📌 {dim}", expanded=True):
            try:
                values = get_distinct_values(dim)
                selected = st.multiselect(
                    f"เลือกค่า {dim}",
                    options=values,
                    key=f"filter_{dim}",
                )
                if selected:
                    dim_filters[dim] = selected
            except Exception as e:
                st.warning(f"โหลดค่าของ {dim} ไม่ได้: {e}")

    st.divider()
    st.subheader("📊 Summary Measures")
    selected_measures = st.multiselect(
        "เลือก Measure ที่ต้องการใน Summary",
        options=list(MEASURES.keys()),
        default=["total_port","total_port_acct","nea","amt_30plus","amt_90plus","write_off"],
        format_func=lambda x: f"{x} ({MEASURES[x]})",
    )

    st.divider()
    st.subheader("📋 Columns ในตาราง")
    display_cols = st.multiselect(
        "เลือก Column ที่แสดงในตาราง",
        options=DIMENSIONS + list(MEASURES.keys()),
        default=DEFAULT_DISPLAY_COLS,
    )

    st.divider()
    max_rows = st.number_input(
        "จำกัดจำนวนแถว", min_value=100, max_value=1000000,
        value=50000, step=1000,
        help="ป้องกัน Excel เกิน limit"
    )

    run_btn = st.button("🔄 ดึงข้อมูล", type="primary", use_container_width=True)

# ── Build SQL ──────────────────────────────────────────────────────────────
def build_sql(
    data_months: list,
    dim_filters: dict,
    display_cols: list,
    max_rows: int,
) -> str:
    def q(name):
        import re
        if re.search(r'[^a-zA-Z0-9_]', name) or re.match(r'^\d', name):
            return f"`{name}`"
        return name

    # แยก column เป็น dim หรือ measure
    select_parts = []
    for col in display_cols:
        if col in MEASURES:
            src_col = col  # ชื่อ alias ตรงกับ column ใน table
            select_parts.append(f"sum({q(src_col)}) as {q(col)}")
        else:
            select_parts.append(q(col))

    # GROUP BY เฉพาะ dims
    group_dims = [c for c in display_cols if c not in MEASURES]

    # WHERE
    where_parts = []

    # data_month
    months_str = ",".join(m.strip() for m in data_months)
    where_parts.append(f"data_month in ({months_str})")

    # dimension filters
    for dim, vals in dim_filters.items():
        vals_str = ",".join(f"'{v}'" for v in vals)
        where_parts.append(f"lower({q(dim)}) in ({','.join(f'lower({chr(39)}{v}{chr(39)})' for v in vals)})")

    where_clause = "where " + "\n  and ".join(where_parts)
    select_clause = "\n, ".join(select_parts)
    group_clause = "\n, ".join(q(d) for d in group_dims) if group_dims else "1"

    has_measure = any(c in MEASURES for c in display_cols)

    if has_measure:
        sql = f"""
select
  {select_clause}
from {TABLE}
{where_clause}
group by
  {group_clause}
limit {max_rows}
""".strip()
    else:
        sql = f"""
select
  {select_clause}
from {TABLE}
{where_clause}
limit {max_rows}
""".strip()

    return sql

# ── Main: Run query ────────────────────────────────────────────────────────
if run_btn:
    # validate data_month
    data_months = [m.strip() for m in data_month_input.split(",") if m.strip()]
    if not data_months:
        st.error("กรุณากรอก data_month อย่างน้อย 1 เดือน")
        st.stop()

    # build SQL
    final_cols = display_cols if display_cols else DEFAULT_DISPLAY_COLS
    sql = build_sql(data_months, dim_filters, final_cols, int(max_rows))

    with st.expander("🔎 SQL ที่ใช้", expanded=False):
        st.code(sql, language="sql")

    with st.spinner("⏳ กำลังดึงข้อมูลจาก Databricks..."):
        try:
            df = run_query(sql)
        except Exception as e:
            st.error(f"Query error: {e}")
            st.stop()

    if df.empty:
        st.warning("ไม่พบข้อมูลตาม filter ที่เลือก")
        st.stop()

    st.success(f"✅ พบ **{len(df):,}** แถว")

    # ── Summary metrics ────────────────────────────────────────────────────
    if selected_measures:
        st.subheader("📊 Summary")
        avail = [m for m in selected_measures if m in df.columns]
        if avail:
            cols = st.columns(min(len(avail), 4))
            for i, m in enumerate(avail):
                val = df[m].sum()
                label = MEASURES.get(m, m)
                cols[i % 4].metric(label, f"{val:,.0f}")

        # Ratio measures
        ratio_avail = {}
        for ratio_name, (num, den) in RATIO_MEASURES.items():
            if num in df.columns and den in df.columns:
                total_num = df[num].sum()
                total_den = df[den].sum()
                if total_den > 0:
                    ratio_avail[ratio_name] = total_num / total_den * 100

        if ratio_avail:
            st.caption("📐 Ratio Measures (คำนวณจาก summary)")
            rcols = st.columns(min(len(ratio_avail), 4))
            for i, (name, val) in enumerate(ratio_avail.items()):
                rcols[i % 4].metric(name, f"{val:.2f}%")

    # ── Table ──────────────────────────────────────────────────────────────
    st.subheader("📋 รายละเอียดบัญชี")

    # Format number columns
    num_cols = df.select_dtypes(include="number").columns.tolist()
    fmt = {c: "{:,.2f}" for c in num_cols}

    st.dataframe(
        df.style.format(fmt, na_rep="-"),
        use_container_width=True,
        height=500,
    )

    # ── Download ───────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Account_Drill")
        st.download_button(
            label="⬇️ Download Excel",
            data=buf.getvalue(),
            file_name=f"account_drill_{'_'.join(data_months)}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col2:
        csv_data = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name=f"account_drill_{'_'.join(data_months)}.csv",
            mime="text/csv",
            use_container_width=True,
        )

else:
    st.info("👈 กรอก filter ทางซ้าย แล้วกด **ดึงข้อมูล**")
    st.markdown("""
    **วิธีใช้:**
    1. กรอก `data_month` (บังคับ) เช่น `202607` หรือหลายเดือน `202606,202607`
    2. เลือก Dimension ที่ต้องการ filter (optional)
    3. เลือกค่าของแต่ละ Dimension
    4. เลือก Measure ที่ต้องการดูใน Summary
    5. เลือก Column ที่ต้องการแสดงในตาราง
    6. กดปุ่ม **ดึงข้อมูล**
    7. Download Excel หรือ CSV ได้เลย
    """)
