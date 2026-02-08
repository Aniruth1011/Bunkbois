import pandas as pd

# Input CSV
input_file = "us_healthcare_data_doctors.csv"

# Output files
specialty_file = "unique_specialties.txt"
department_file = "unique_departments.txt"

# Read CSV
df = pd.read_csv(input_file)

# Unique specialties
unique_specialties = (
    df["specialty"]
    .dropna()
    .astype(str)
    .str.strip()
    .drop_duplicates()
    .sort_values()
)

# Unique departments
unique_departments = (
    df["department"]
    .dropna()
    .astype(str)
    .str.strip()
    .drop_duplicates()
    .sort_values()
)

# Save to text files
unique_specialties.to_csv(specialty_file, index=False, header=False)
unique_departments.to_csv(department_file, index=False, header=False)

print(f"Saved {len(unique_specialties)} specialties to {specialty_file}")
print(f"Saved {len(unique_departments)} departments to {department_file}")
