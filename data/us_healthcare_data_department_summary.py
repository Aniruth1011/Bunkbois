import pandas as pd

# Input CSV
input_file = "us_healthcare_data_department_summary.csv"

# Output files
hospital_file = "unique_hospitals.txt"
department_file = "unique_departments.txt"

# Read CSV
df = pd.read_csv(input_file)

# Extract unique hospital names
unique_hospitals = (
    df["affiliated_hospital_name"]
    .dropna()
    .astype(str)
    .str.strip()
    .drop_duplicates()
    .sort_values()
)

# Extract unique departments
unique_departments = (
    df["department"]
    .dropna()
    .astype(str)
    .str.strip()
    .drop_duplicates()
    .sort_values()
)

# Save hospital names
unique_hospitals.to_csv(hospital_file, index=False, header=False)

# Save departments
unique_departments.to_csv(department_file, index=False, header=False)

print(f"Saved {len(unique_hospitals)} hospitals to {hospital_file}")
print(f"Saved {len(unique_departments)} departments to {department_file}")
