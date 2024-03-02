import re
import json

# Load the JSON data
with open('facebook_friends_data.json', 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)

# Words to remove from links
remove_list = ["mutual", "marketplace", "app_tab", "about", "friends", "photos", "videos", "map", 
               "friends_all", "friends_recent", "friends_with_upcoming_birthdays", "following", "create", 
               "photo", "groups", "bookmarks", "notifications","sports","books","athlets"]

# Define the regular expression pattern
pattern = r'^\s*{\s*"link":\s*"(https://www\.facebook\.com/[^"]*)",\s*"text":\s*".+"\s*}\s*$'

# Filter out entries with links containing specified words
filtered_data = [entry for entry in data if not any(word in entry["link"] for word in remove_list)]

# Extract the data matching the pattern and remove entries with an empty "text" field
filtered_data = [entry for entry in filtered_data if re.match(pattern, json.dumps(entry, indent=None, separators=(',', ':')), flags=re.MULTILINE) and entry["text"] != ""]

# Remove the "https://www.facebook.com" part from the links
for entry in filtered_data:
    entry["link"] = entry["link"].replace("https://www.facebook.com", "")

# Convert the list to a set to remove duplicates and then back to a list
unique_filtered_data = list(set(json.dumps(entry, indent=None, separators=(',', ':')) for entry in filtered_data))

# Write the unique filtered data to a new file
with open('unique_filtered_data.json', 'w', encoding='utf-8') as new_file:
    new_file.write("[\n")
    new_file.write(",\n".join(unique_filtered_data))
    new_file.write("\n]")
