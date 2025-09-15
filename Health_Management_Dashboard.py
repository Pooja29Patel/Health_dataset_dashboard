import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.io as pio

# =====================
# Load Data
# =====================
df = pd.read_excel("Health_Management_Project.xlsx", sheet_name="Cleaned Data")

# Normalize column names
df.columns = df.columns.str.strip()
df = df.rename(columns={
    "Patient ID": "Patient_ID",
    "Appointment Date": "Appointment_Date",
    "Checkup Status": "Status",
    "Bill Amount": "Bill_Amount",
    "Payment Status": "Payment_Status",
    "Follow-Up Required": "FollowUp_Required",
    "Satisfaction Score": "Satisfaction_Score"
})

df["Appointment_Date"] = pd.to_datetime(df["Appointment_Date"], errors="coerce")
df["Month"] = df["Appointment_Date"].dt.to_period("M").astype(str)
df["DayOfWeek"] = df["Appointment_Date"].dt.day_name()

def bmi_bucket(bmi):
    if pd.isna(bmi): return "Unknown"
    if bmi < 18.5: return "Underweight"
    if bmi < 25: return "Normal"
    if bmi < 30: return "Overweight"
    return "Obesity"

df["BMI_Category"] = df["BMI"].apply(bmi_bucket)

# =====================
# Sidebar Filters
# =====================
st.sidebar.header("Filters")

doctors = st.sidebar.multiselect("Select Doctor(s)", df["Doctor"].unique())
cities = st.sidebar.multiselect("Select City(s)", df["City"].unique())
genders = st.sidebar.multiselect("Select Gender(s)", df["Gender"].unique())
diagnoses = st.sidebar.multiselect("Select Diagnosis", df["Diagnosis"].unique())
insurance = st.sidebar.multiselect("Select Insurance Status", df["Insurance Status"].unique())

filtered_df = df.copy()
if doctors: filtered_df = filtered_df[filtered_df["Doctor"].isin(doctors)]
if cities: filtered_df = filtered_df[filtered_df["City"].isin(cities)]
if genders: filtered_df = filtered_df[filtered_df["Gender"].isin(genders)]
if diagnoses: filtered_df = filtered_df[filtered_df["Diagnosis"].isin(diagnoses)]
if insurance: filtered_df = filtered_df[filtered_df["Insurance Status"].isin(insurance)]

# =====================
# KPIs
# =====================
st.title("🏥 Healthcare Analytics Dashboard – Pooja Patel")

col1, col2, col3, col4, col5 = st.columns(5)
with col1: st.metric("Total Patients", filtered_df["Patient_ID"].nunique())
with col2:
    chronic_pct = (filtered_df[filtered_df["Diagnosis"].isin(["Hypertension","Diabetes","Obesity"])]["Patient_ID"].nunique() / 
                   filtered_df["Patient_ID"].nunique() * 100) if len(filtered_df) else 0
    st.metric("Chronic Patients %", f"{chronic_pct:.2f}%")
with col3:
    missed_pct = (filtered_df["Status"].eq("Missed").sum()/len(filtered_df)*100) if len(filtered_df) else 0
    st.metric("Missed Appointments %", f"{missed_pct:.2f}%")
with col4:
    revenue = pd.to_numeric(filtered_df["Bill_Amount"], errors="coerce").fillna(0).sum()
    st.metric("Total Revenue", f"{revenue:,.0f}")
with col5:
    avg_sat = pd.to_numeric(filtered_df["Satisfaction_Score"], errors="coerce").mean()
    st.metric("Avg Satisfaction", f"{avg_sat:.2f}" if not np.isnan(avg_sat) else "N/A")

# =====================
# Charts with Insights
# =====================
st.subheader("📊 Visual Insights")

fig_list = []  # Store figures for download

# 1. Appointments Over Time
appt_over_time = filtered_df.groupby("Appointment_Date").size().reset_index(name="Appointment_Count")
if not appt_over_time.empty:
    fig1 = px.line(appt_over_time, x="Appointment_Date", y="Appointment_Count", title="Appointments Over Time", markers=True)
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown(f"**Insight:** Peak appointment day: {appt_over_time.loc[appt_over_time['Appointment_Count'].idxmax(),'Appointment_Date'].date()} with {appt_over_time['Appointment_Count'].max()} appointments.")
    fig_list.append(fig1)
else:
    fig_list.append(None)

# 2. Monthly Revenue
monthly_rev = filtered_df.groupby("Month")["Bill_Amount"].sum().reset_index()
if not monthly_rev.empty:
    fig2 = px.bar(monthly_rev, x="Month", y="Bill_Amount", title="Monthly Revenue Breakdown", color="Bill_Amount")
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown(f"**Insight:** Highest revenue month: {monthly_rev.loc[monthly_rev['Bill_Amount'].idxmax(),'Month']} (${monthly_rev['Bill_Amount'].max():,.0f})")
    fig_list.append(fig2)
else:
    fig_list.append(None)

# 3. Diagnosis Breakdown
diag_ct = filtered_df["Diagnosis"].value_counts().reset_index()
diag_ct.columns = ["Diagnosis", "Patient_Count"]
if not diag_ct.empty:
    fig3 = px.bar(diag_ct, x="Patient_Count", y="Diagnosis", orientation="h", title="Patient Count by Diagnosis", color="Patient_Count")
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown(f"**Insight:** Most common diagnosis: {diag_ct.loc[diag_ct['Patient_Count'].idxmax(),'Diagnosis']} ({diag_ct['Patient_Count'].max()} patients)")
    fig_list.append(fig3)
else:
    fig_list.append(None)

# 4. BMI Distribution
bmi_ct = filtered_df["BMI_Category"].value_counts().reset_index()
bmi_ct.columns = ["BMI_Category", "Count"]
if not bmi_ct.empty:
    fig4 = px.pie(bmi_ct, names="BMI_Category", values="Count", hole=0.4, title="BMI Distribution")
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown(f"**Insight:** Majority BMI category: {bmi_ct.loc[bmi_ct['Count'].idxmax(),'BMI_Category']} ({bmi_ct['Count'].max()} patients)")
    fig_list.append(fig4)
else:
    fig_list.append(None)

# 5. Follow-Up Required
fu_ct = filtered_df["FollowUp_Required"].value_counts().reset_index()
fu_ct.columns = ["FollowUp_Required", "Count"]
if not fu_ct.empty:
    fig5 = px.bar(fu_ct, x="FollowUp_Required", y="Count", title="Follow-Up Required", color="Count")
    st.plotly_chart(fig5, use_container_width=True)
    st.markdown(f"**Insight:** Most follow-up status: {fu_ct.loc[fu_ct['Count'].idxmax(),'FollowUp_Required']} ({fu_ct['Count'].max()} cases)")
    fig_list.append(fig5)
else:
    fig_list.append(None)

# =====================
# Export Options
# =====================
# Download filtered data
st.sidebar.download_button(
    label="📥 Download Filtered Data",
    data=filtered_df.to_csv(index=False).encode("utf-8"),
    file_name="filtered_health_data.csv",
    mime="text/csv"
)

# Download charts safely
st.sidebar.markdown("### 📊 Download Charts")
for i, fig in enumerate(fig_list, start=1):
    if fig:  # Only add download button if figure exists
        st.sidebar.download_button(
            label=f"Download Chart {i}",
            data=pio.to_image(fig, format="png"),
            file_name=f"chart_{i}.png",
            mime="image/png"
        )

# =====================
# AI / Analytics Note
# =====================
st.sidebar.markdown("""
### 🧠 Analytics Logic
- Patient KPIs: total patients, chronic %, missed appointments %, revenue, satisfaction.
- Diagnosis & BMI trends analyzed using aggregation and visualization.
- Insights derived from descriptive statistics and trend analysis.
- Streamlit provides interactive filtering to customize analysis by doctor, city, gender, diagnosis, and insurance.
""")
