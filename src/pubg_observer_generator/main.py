import csv
import os
import re
import shutil
import sys
from collections import Counter

from PIL import Image, ImageDraw, ImageFont


def hex_to_ansi_color(hex_color):
    # Convert hex to RGB values
    r = int(hex_color[:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    # Return ANSI escape code for colors
    return f"\033[38;2;{r};{g};{b}m"


def reset_color():
    return "\033[0m"


def format_row_with_color(row):
    team_number, team_name, team_short_name, image_file_name, color = row
    # Take color code without an FF suffix
    hex_color = color[:-2]
    ansi_color = hex_to_ansi_color(hex_color)
    # Format row so that color code is displayed in its color
    return f"{team_number}, {team_name}, {team_short_name}, {image_file_name}, {ansi_color}{color}{reset_color()}"


def is_black_or_close(color, threshold=30):
    # Check if the color is black or close to black
    return all(c <= threshold for c in color[:3])


def is_white_or_close(color, threshold=225):
    # Check if the color is white or close to white
    return all(c >= threshold for c in color[:3])


def _calculate_saturation(rgb):
    """Calculate color saturation (max - min RGB value)."""
    return max(rgb) - min(rgb)


def dominant_color(image_path):
    image = Image.open(image_path)
    image = image.convert("RGBA")
    colors = image.getdata()

    # Filter out completely transparent pixels (RGBA = 0,0,0,0)
    opaque_colors = [
        color for color in colors if color[3] != 0 and color != (0, 0, 0, 0)
    ]

    if not opaque_colors:
        return 0, 0, 0  # Return black if no colors found

    # Sort colors by frequency
    color_count = Counter(opaque_colors)
    most_common_colors = color_count.most_common()

    # Collect all acceptable colors (those not too close to black/white)
    acceptable_colors = []
    for color, count in most_common_colors:
        rgb = color[:3]
        if not is_black_or_close(color, threshold=50) and not is_white_or_close(
            color, threshold=200
        ):
            saturation = _calculate_saturation(rgb)
            acceptable_colors.append((color, count, saturation))

    # If acceptable colors are found, select the most saturated one
    if acceptable_colors:
        acceptable_colors.sort(key=lambda x: x[2], reverse=True)
        return acceptable_colors[0][0][:3]

    # If no acceptable colors are found, select the most saturated from all colors
    print(
        f"⚠️ Warning: No acceptable colors found in {image_path}, selecting most saturated from all colors"
    )

    # Calculate saturation for all colors and sort by the highest saturation
    all_colors_with_saturation = [
        (color, count, _calculate_saturation(color[:3]))
        for color, count in most_common_colors
    ]
    all_colors_with_saturation.sort(key=lambda x: x[2], reverse=True)

    return all_colors_with_saturation[0][0][:3]


def rgb_to_hex(rgb):
    # Convert RGB to hex format without # symbol and add FF at the end
    return f"{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}FF".upper()


def add_slot_number_to_image(image_path, slot_number, output_path=None):
    """Add slot number to image in bottom-right corner with white text and black outline."""
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    # Try to load fonts in order of preference
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Narrow Bold Italic.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]

    font = None
    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, 300)
            break
        except OSError:
            continue

    if font is None:
        font = ImageFont.load_default()

    text = str(slot_number)

    # Calculate text position (bottom-right corner with margins)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = image.width - text_width - 30
    y = image.height - text_height - 80

    # Add text with black outline
    draw.text(
        (x, y), text, font=font, fill="white", stroke_fill="black", stroke_width=8
    )

    output_path = output_path or image_path
    image.save(output_path)


def create_team_short_name(team_name):
    # Parse name into words
    words = re.findall(r"[a-zA-Z0-9]+", team_name)

    if not words:
        return "XXXX"  # Fallback if no words

    first_word = words[0]

    # Rule 1: Use 4 characters from the first word
    # Rule 2: If the word is less than 4 characters, then use the whole word
    if len(first_word) >= 4:
        return first_word[:4].upper()
    else:
        return first_word.upper()


def resolve_short_name_conflicts(team_names):
    """
    Resolve short name conflicts using progressive conflict resolution:
    1) Use three chars from the first word and one from the second
    2) If still same, then use two chars from the first word and two from the second
    3) If still conflict or can't use second word then use unique char as the fourth char
    """
    # Create all abbreviations first
    short_names = {}
    conflicts = {}

    for team_name in team_names:
        base_short = create_team_short_name(team_name)
        if base_short in short_names:
            # Conflict found, add to list
            if base_short not in conflicts:
                conflicts[base_short] = [short_names[base_short]]
            conflicts[base_short].append(team_name)
        else:
            short_names[base_short] = team_name

    # Resolve conflicts
    final_short_names = {}

    # First, add all non-conflicting teams
    for short_name, team_name in short_names.items():
        if short_name not in conflicts:
            # No conflict, use original
            final_short_names[team_name] = short_name

    # Then resolve conflicts
    for short_name, conflicting_list in conflicts.items():
        conflicting_teams = list(
            set([short_names.get(short_name)] + conflicting_list)
        )  # Include the original team too

        # Remove None values
        conflicting_teams = [team for team in conflicting_teams if team is not None]

        # Keep track of all used short names (including those already resolved)
        all_used_names = set(final_short_names.values())

        # Try each strategy for all teams in the conflict group
        resolved_names = {}

        # Strategy 1: Use 3 chars from first word + 1 from second word
        strategy1_results = {}
        for team in conflicting_teams:
            words = re.findall(r"[a-zA-Z0-9]+", team)
            first_word = words[0] if words else ""

            if len(words) >= 2 and len(words[1]) > 0:
                new_short = (first_word[:3] + words[1][0]).upper()[:4]
                if new_short not in all_used_names:
                    strategy1_results[team] = new_short

        # Check if strategy 1 creates unique names for all teams
        strategy1_values = list(strategy1_results.values())
        if len(strategy1_values) == len(set(strategy1_values)) and len(
            strategy1_results
        ) == len(conflicting_teams):
            # Strategy 1 works, use it
            resolved_names.update(strategy1_results)
            all_used_names.update(strategy1_values)
        else:
            # Strategy 1 creates duplicates or doesn't cover all teams, try strategy 2
            strategy2_results = {}
            for team in conflicting_teams:
                words = re.findall(r"[a-zA-Z0-9]+", team)
                first_word = words[0] if words else ""

                if len(words) >= 2 and len(words[1]) >= 2:
                    new_short = (first_word[:2] + words[1][:2]).upper()[:4]
                    if new_short not in all_used_names:
                        strategy2_results[team] = new_short

            # Check if strategy 2 creates unique names for all teams
            strategy2_values = list(strategy2_results.values())
            if len(strategy2_values) == len(set(strategy2_values)) and len(
                strategy2_results
            ) == len(conflicting_teams):
                # Strategy 2 works, use it
                resolved_names.update(strategy2_results)
                all_used_names.update(strategy2_values)
            else:
                # Fall back to individual resolution for each team
                for team in conflicting_teams:
                    words = re.findall(r"[a-zA-Z0-9]+", team)
                    first_word = words[0] if words else ""

                    resolved = False

                    # Try strategy 1 for this specific team
                    if not resolved and len(words) >= 2 and len(words[1]) > 0:
                        new_short = (first_word[:3] + words[1][0]).upper()[:4]
                        if (
                            new_short not in all_used_names
                            and new_short not in resolved_names.values()
                        ):
                            resolved_names[team] = new_short
                            all_used_names.add(new_short)
                            resolved = True

                    # Try strategy 2 for this specific team
                    if not resolved and len(words) >= 2 and len(words[1]) >= 2:
                        new_short = (first_word[:2] + words[1][:2]).upper()[:4]
                        if (
                            new_short not in all_used_names
                            and new_short not in resolved_names.values()
                        ):
                            resolved_names[team] = new_short
                            all_used_names.add(new_short)
                            resolved = True

                    # Strategy 3: Use unique character from the second / third word or generate
                    if not resolved:
                        unique_char = None

                        # Try characters from the second word
                        if len(words) >= 2:
                            for char in words[1]:
                                test_short = (first_word[:3] + char).upper()[:4]
                                if (
                                    test_short not in all_used_names
                                    and test_short not in resolved_names.values()
                                ):
                                    unique_char = char
                                    break

                        # Try characters from third word if second didn't work
                        if unique_char is None and len(words) >= 3:
                            for char in words[2]:
                                test_short = (first_word[:3] + char).upper()[:4]
                                if (
                                    test_short not in all_used_names
                                    and test_short not in resolved_names.values()
                                ):
                                    unique_char = char
                                    break

                        # Generate unique character (numbers 1-9, then letters)
                        if unique_char is None:
                            for char in "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                                test_short = (first_word[:3] + char).upper()[:4]
                                if (
                                    test_short not in all_used_names
                                    and test_short not in resolved_names.values()
                                ):
                                    unique_char = char
                                    break

                        # Apply the resolution
                        if unique_char:
                            new_short = (first_word[:3] + unique_char).upper()[:4]
                            resolved_names[team] = new_short
                            all_used_names.add(new_short)
                        else:
                            # Ultimate fallback - this shouldn't happen
                            resolved_names[team] = (first_word[:3] + "X").upper()[:4]

        # Add resolved names to a final result
        final_short_names.update(resolved_names)

    return final_short_names


def get_team_colors(slots_file):
    team_names = []
    team_data = {}

    # Read all team data first
    with open(slots_file) as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            parts = line.split(maxsplit=1)
            if len(parts) < 2:  # Ensure we get the team number and name
                print(f"Skipping invalid line: {line}")
                continue
            team_number, team_name = parts  # Assume team number and name are separated
            team_number = team_number.strip(".")  # Remove period from the number
            team_names.append(team_name)
            team_data[team_name] = team_number

    # Resolve short name conflicts
    short_names = resolve_short_name_conflicts(team_names)

    # Create the final team_colors dictionary
    team_colors = {}
    for team_name in team_names:
        team_number = team_data[team_name]
        team_short_name = short_names[team_name]
        image_file_name = f"{team_number}.png"  # Create image filename
        team_colors[team_name] = (team_number, team_short_name, image_file_name)

    return team_colors


def prepare_team_data(observer_dir, team_colors, output_observer_dir):
    team_data = []
    used_colors = set()

    # Create TeamIcon directory in output location
    team_icon_dir = os.path.join(output_observer_dir, "TeamIcon")
    os.makedirs(team_icon_dir, exist_ok=True)

    # Collect all colors from clean images first
    for team_name, (
        team_number,
        team_short_name,
        image_file_name,
    ) in team_colors.items():
        # Find clean image in logos directory or TeamIcon directory
        logos_dir = os.path.join(observer_dir, "logos")
        clean_image_path = os.path.join(logos_dir, image_file_name)

        # If the logos directory doesn't exist, use the TeamIcon directory
        if not os.path.isfile(clean_image_path):
            clean_image_path = os.path.join(observer_dir, "TeamIcon", image_file_name)
            if not os.path.isfile(clean_image_path):
                print(
                    f"⚠️ Warning: Could not find image {image_file_name} in logos/ or TeamIcon/"
                )
                continue

        # Analyze color from a clean image
        dom_color = dominant_color(clean_image_path)
        color_hex = rgb_to_hex(dom_color)

        # If color is already used, modify it slightly
        original_color = dom_color
        offset = 0
        while color_hex in used_colors:
            # Change color slightly until we find a unique one
            r = (original_color[0] + offset) % 256
            g = (original_color[1] + offset) % 256
            b = (original_color[2] + offset) % 256
            dom_color = (r, g, b)
            color_hex = rgb_to_hex(dom_color)
            offset += 5  # Increase offset enough to make color visibly different

        used_colors.add(color_hex)

        # Create numbered image in TeamIcon directory
        numbered_image_path = os.path.join(team_icon_dir, image_file_name)
        add_slot_number_to_image(clean_image_path, team_number, numbered_image_path)

        team_data.append(
            [team_number, team_name, team_short_name, image_file_name, color_hex]
        )

    return team_data


def save_new_colors(csv_file, team_data):
    with open(csv_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["TeamNumber", "TeamName", "TeamShortName", "ImageFileName", "TeamColor"]
        )  # Header row
        writer.writerows(team_data)


def create_zip_archive(source_dir, output_zip):
    """Create a zip archive from a directory."""
    shutil.make_archive(output_zip.replace(".zip", ""), "zip", source_dir)


def main():
    if len(sys.argv) != 4:  # Check that all three parameters are provided
        print("❌ Error: Invalid arguments")
        print("Usage: poetry run generator <league_name> <season> <division>")
        print("Example: poetry run generator league_name s15 div4")
        sys.exit(1)

    league_name = sys.argv[1]
    season = sys.argv[2]
    division = sys.argv[3]

    # Create an input directory path
    observer_dir = os.path.join("content", league_name, season, division)
    if not os.path.isdir(observer_dir):  # Check that the directory exists
        print(f"❌ Error: Directory not found: {observer_dir}")
        print(
            "Please ensure your images are organized as: content/league_name/season/division/"
        )
        sys.exit(1)

    # Define file paths
    slots_file = os.path.join(observer_dir, "Slots.txt")
    if not os.path.isfile(slots_file):  # Check that Slots.txt exists
        print(f"❌ Error: File not found: {slots_file}")
        sys.exit(1)

    # Create output directory structure
    output_base_name = f"{league_name}-{season}-{division}"
    generated_dir = os.path.join("content", "generated", output_base_name)
    observer_output_dir = os.path.join(generated_dir, "Observer")

    # Create directories
    os.makedirs(observer_output_dir, exist_ok=True)

    # Define TeamInfo.csv file path (will be created later)
    csv_file = os.path.join(observer_output_dir, "TeamInfo.csv")

    team_colors = get_team_colors(slots_file)
    team_data = prepare_team_data(observer_dir, team_colors, observer_output_dir)

    # Show summary
    print("\nPrepared data for CSV:")
    print("TeamNumber, TeamName, TeamShortName, ImageFileName, TeamColor")
    print("-" * 70)
    for row in team_data:
        print(format_row_with_color(row))

    # Create TeamInfo.csv
    save_new_colors(csv_file, team_data)

    # Create a zip archive (only Observer folder contents)
    zip_file = os.path.join(generated_dir, f"{output_base_name}.zip")
    create_zip_archive(observer_output_dir, zip_file)

    print(f"\n✅ Generated files in: {generated_dir}")
    print(f"📦 Zip archive created: {zip_file}")


if __name__ == "__main__":
    main()
