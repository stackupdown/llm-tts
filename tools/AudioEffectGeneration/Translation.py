import json
from translate import Translator

# Create a translator object
translator = Translator(from_lang='zh', to_lang='en')

# Define file paths
input_json_path = "output_addid.json"
translated_json_path = "output_translated.json"
mapping_txt_path = "sound_mapping.txt"


# Load JSON file
def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Save JSON file
def save_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# Save mapping to txt file
def save_mapping(mapping, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        for tid, sound_text, translation in mapping:
            f.write(f"{tid}\t{sound_text}\t{translation}\n")


# Translate and update JSON data
def translate_and_update(json_data):
    sound_mapping = []  # List to store sound translations
    for cell in json_data:
        tid = cell.get("tid", "")
        sound_text = cell.get("sound", "").strip()

        if sound_text not in ["", "无"]:
            try:
                translation = translator.translate(sound_text)
                if not translation:  # Handle empty translation
                    translation = "Unknown"
            except Exception as e:
                print(f"Error translating '{sound_text}': {e}")
                translation = "Error"

            # Append to the mapping list
            sound_mapping.append((tid, sound_text, translation))

            # Update the sound field in the JSON data
            cell["sound"] = translation
        else:
            cell["sound"] = "None"  # Standardize empty or "无" to "None"

    return json_data, sound_mapping


# Main function
def main():
    try:
        # Load JSON data
        json_data = load_json(input_json_path)

        # Translate and update JSON data
        updated_json_data, sound_mapping = translate_and_update(json_data)

        # Save updated JSON data
        save_json(updated_json_data, translated_json_path)
        print(f"Translated JSON saved to {translated_json_path}")

        # Save mapping to txt file
        save_mapping(sound_mapping, mapping_txt_path)
        print(f"Sound mapping saved to {mapping_txt_path}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
