import pandas as pd

# Load CSV
df = pd.read_csv("us_healthcare_data_hospitals.csv")

capability_file = "capabilities.txt"
facility_file = "facility_types.txt"

with open(capability_file, "w", encoding="utf-8") as cap_f, \
     open(facility_file, "w", encoding="utf-8") as fac_f:

    for _, row in df.iterrows():
        capability = str(row.get("capability", "")).strip()
        facility_type = str(row.get("facilityTypeId", "")).strip()

        cap_f.write(capability + "\n")
        fac_f.write(facility_type + "\n")

print("Files created:")
print(capability_file)
print(facility_file)
