import os

def clean_and_split(input_file, output_file):
    cleaned = set()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Skip empty or nan lines
            if not line or line.lower() == "nan":
                continue

            # Split on comma and take the first part
            primary = line.split(",")[0].strip()
            cleaned.add(primary)

    # Write sorted unique results
    with open(output_file, "w", encoding="utf-8") as f:
        for item in sorted(cleaned):
            f.write(item + "\n")

    print(f"Saved {len(cleaned)} unique cleaned entries to {output_file}")

clean_and_split( "clean/cleaned_unique_specialties.txt", "clean2/cleaned_unique_specialties.txt" ) 
clean_and_split( "clean/cleaned_capabilities.txt", "clean2/cleaned_capabilities.txt" ) 
clean_and_split( "clean/cleaned_unique_departments.txt", "clean2/cleaned_unique_departments.txt" ) 
clean_and_split( "clean/cleaned_unique_hospitals.txt", "clean2/cleaned_unique_hospitals.txt" ) 
clean_and_split( "clean/cleaned_facility_types.txt", "clean2/cleaned_facility_types.txt" )