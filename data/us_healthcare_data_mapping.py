import pandas as pd
import json

# Input CSV
input_file = "us_healthcare_data_hospital_doctor_mapping.csv"

# Output JSON
output_file = "hospital_id_to_name.json"

# Read CSV
df = pd.read_csv(input_file)

# Keep only required columns and drop duplicates/nulls
hospital_map_df = (
    df[["hospital_id", "hospital_name"]]
    .dropna()
    .drop_duplicates()
)

# Convert to dictionary
hospital_map = dict(
    zip(
        hospital_map_df["hospital_id"].astype(str),
        hospital_map_df["hospital_name"]
    )
)

# Save as JSON
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(hospital_map, f, indent=2, ensure_ascii=False)

print(f"Saved {len(hospital_map)} hospital mappings to {output_file}")
