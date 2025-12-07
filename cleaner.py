input_path = "C:/Users/User/Downloads/loop/utf8-Reviews.csv"
output_path = "C:/Users/User/Downloads/loop/Reviews_clean.csv"

# List of all Windows-1252 invalid bytes that break UTF-8
invalid_bytes = bytes([0x81, 0x8D, 0x8F, 0x90, 0x9D])

with open(input_path, "rb") as src, open(output_path, "wb") as dst:
    for line in src:
        clean_line = line.translate(None, invalid_bytes)  # REMOVE them
        dst.write(clean_line)

print("Cleaning complete! Saved as Reviews_clean.csv")
