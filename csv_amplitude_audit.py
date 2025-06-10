import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
import numpy as np

file_name = "FordPass & Lincoln Way [Live]_events_2025-06-09T17_55_51.078+00_00.csv"
# Load your CSV file
df = pd.read_csv(file_name)

# Step 1: Filter to valid event rows
strict_event_rows = df[
    (df["Action"].str.upper() != "IGNORE") &
    (df["Object Type"].str.upper() == "EVENT") &
    (df["Event Activity"].str.upper() == "ACTIVE") &
    (df["Event Category"].str.upper() != "ERRONEOUS") &
    (~df["Event Schema Status"].str.upper().isin(["DELETED", "BLOCKED"]))
].copy()

# Step 2: Normalize and split Tags column into list
def parse_tags(tag_str):
    if pd.isna(tag_str):
        return []
    return [tag.strip().lower() for tag in tag_str.split(',')]

strict_event_rows["parsed_tags"] = strict_event_rows["Tags"].apply(parse_tags)

# Step 3: Boolean flags for audit
strict_event_rows["has_pm_pass"] = strict_event_rows["parsed_tags"].apply(lambda tags: "pm pass" in tags)
strict_event_rows["has_qa_pass"] = strict_event_rows["parsed_tags"].apply(lambda tags: "qa pass" in tags)
strict_event_rows["has_qa_fail"] = strict_event_rows["parsed_tags"].apply(lambda tags: "qa fail" in tags)
strict_event_rows["has_qa_tag"] = strict_event_rows["has_qa_pass"] | strict_event_rows["has_qa_fail"]

# Step 4: Normalize Event Category
strict_event_rows["Event Category"] = strict_event_rows["Event Category"]\
    .fillna("Uncategorized")\
    .astype(str)\
    .str.strip()\
    .str.title()

# NEW: Step 4.5: Assign Pillar based on Event Category (space-delimited)
def assign_pillar(category):
    """Assign pillar based on event category prefix (space-delimited)"""
    if pd.isna(category):
        return 'Uncategorized'
    
    category_str = str(category).strip()
    
    # Split by space and check first word
    parts = category_str.split(' ', 1)  # Split on first space only
    if len(parts) > 0:
        first_word = parts[0].lower()
        
        if first_word == 'core':
            return 'Core'
        elif first_word == 'extension':
            return 'Extension'  
        elif first_word == 'platform':
            return 'Platform'
    
    # Everything else goes to Uncategorized
    return 'Uncategorized'

strict_event_rows["Pillar"] = strict_event_rows["Event Category"].apply(assign_pillar)

# Step 5: Group and summarize (original)
final_summary_df = (
    strict_event_rows.groupby("Event Category")
    .agg(
        Total_Events=("parsed_tags", "size"),
        PM_Missing=("has_pm_pass", lambda x: (~x).sum()),
        QA_Missing=("has_qa_tag", lambda x: (~x).sum()),
        QA_Pass_Count=("has_qa_pass", "sum"),
        QA_Fail_Count=("has_qa_fail", "sum")
    )
    .reset_index()
)

# NEW: Step 5.5: Pillar-level summary for leaders
pillar_summary_df = (
    strict_event_rows.groupby("Pillar")
    .agg(
        Total_Events=("parsed_tags", "size"),
        PM_Missing=("has_pm_pass", lambda x: (~x).sum()),
        QA_Missing=("has_qa_tag", lambda x: (~x).sum()),
        QA_Pass_Count=("has_qa_pass", "sum"),
        QA_Fail_Count=("has_qa_fail", "sum"),
        Categories_Count=("Event Category", "nunique")
    )
    .reset_index()
)

# Step 6: Derived metrics (original)
final_summary_df["QA_Pass_Fail"] = final_summary_df["QA_Pass_Count"] + final_summary_df["QA_Fail_Count"]

final_summary_df["% PM Complete"] = (
    (final_summary_df["Total_Events"] - final_summary_df["PM_Missing"]) /
    final_summary_df["Total_Events"] * 100
).clip(lower=0, upper=100).round(2)

final_summary_df["% QA Pass"] = final_summary_df.apply(
    lambda row: round(
        100 * row["QA_Pass_Count"] / row["Total_Events"],
        2
    ) if row["QA_Pass_Fail"] > 0 else 0,
    axis=1
)

final_summary_df["% QA Tagging Missing"] = (
    final_summary_df["QA_Missing"] / final_summary_df["Total_Events"] * 100
).clip(lower=0, upper=100).round(2)

# NEW: Step 6.5: Derived metrics for pillar summary
pillar_summary_df["QA_Pass_Fail"] = pillar_summary_df["QA_Pass_Count"] + pillar_summary_df["QA_Fail_Count"]

pillar_summary_df["% PM Complete"] = (
    (pillar_summary_df["Total_Events"] - pillar_summary_df["PM_Missing"]) /
    pillar_summary_df["Total_Events"] * 100
).clip(lower=0, upper=100).round(2)

pillar_summary_df["% QA Pass"] = pillar_summary_df.apply(
    lambda row: round(
        100 * row["QA_Pass_Count"] / row["Total_Events"],
        2
    ) if row["QA_Pass_Fail"] > 0 else 0,
    axis=1
)

pillar_summary_df["% QA Tagging Missing"] = (
    pillar_summary_df["QA_Missing"] / pillar_summary_df["Total_Events"] * 100
).clip(lower=0, upper=100).round(2)


# Step 7: Drop zero-event categories (original)
final_summary_df = final_summary_df[final_summary_df["Total_Events"] > 0].copy()

# Step 8: Create total row (original)
total_row = {
    "Event Category": "Total",
    "Total_Events": final_summary_df["Total_Events"].sum(),
    "PM_Missing": final_summary_df["PM_Missing"].sum(),
    "QA_Missing": final_summary_df["QA_Missing"].sum(),
    "QA_Pass_Count": final_summary_df["QA_Pass_Count"].sum(),
    "QA_Fail_Count": final_summary_df["QA_Fail_Count"].sum()
}
total_row["QA_Pass_Fail"] = total_row["QA_Pass_Count"] + total_row["QA_Fail_Count"]
total_row["% PM Complete"] = round(
    100 * (total_row["Total_Events"] - total_row["PM_Missing"]) / total_row["Total_Events"], 2
) if total_row["Total_Events"] > 0 else 0
total_row["% QA Pass"] = round(
    100 * total_row["QA_Pass_Count"] / total_row["Total_Events"], 2
) if total_row["QA_Pass_Fail"] > 0 else 0
total_row["% QA Tagging Missing"] = round(
    100 * total_row["QA_Missing"] / total_row["Total_Events"], 2
) if total_row["Total_Events"] > 0 else 0

# Step 9: Insert total row at the top (original)
total_df = pd.DataFrame([total_row])
final_summary_df = pd.concat([total_df, final_summary_df], ignore_index=True)

# NEW: Create detailed category breakdown by pillar for deeper insights
category_pillar_df = (
    strict_event_rows.groupby(["Pillar", "Event Category"])
    .agg(
        Total_Events=("parsed_tags", "size"),
        PM_Missing=("has_pm_pass", lambda x: (~x).sum()),
        QA_Missing=("has_qa_tag", lambda x: (~x).sum()),
        QA_Pass_Count=("has_qa_pass", "sum"),
        QA_Fail_Count=("has_qa_fail", "sum")
    )
    .reset_index()
)

# Add derived metrics
category_pillar_df["% PM Complete"] = (
    (category_pillar_df["Total_Events"] - category_pillar_df["PM_Missing"]) /
    category_pillar_df["Total_Events"] * 100
).round(2)

category_pillar_df["% QA Tagging Missing"] = (
    category_pillar_df["QA_Missing"] / category_pillar_df["Total_Events"] * 100
).round(2)

category_pillar_df["% QA Pass"] = (
    category_pillar_df["QA_Pass_Count"] / category_pillar_df["Total_Events"] * 100
).round(2)


# Step 10: Save outputs
final_summary_df.to_csv("event_tag_audit_summary.csv", index=False)
strict_event_rows.to_csv("filtered_event_list.csv", index=False)

# NEW: Save pillar-focused outputs
pillar_summary_df.to_csv("pillar_leader_dashboard.csv", index=False)
category_pillar_df.to_csv("category_by_pillar_breakdown.csv", index=False)

# Step 11: Print confirmation
print("✅ Original outputs:")
print("   - Filtered events saved to 'filtered_event_list.csv'")
print("   - Audit summary (with total at top) saved to 'event_tag_audit_summary.csv'")
print("")
print("✅ NEW Leadership-focused outputs:")
print("   - Pillar dashboard saved to 'pillar_leader_dashboard.csv'")
print("   - Category breakdown by pillar saved to 'category_by_pillar_breakdown.csv'")
