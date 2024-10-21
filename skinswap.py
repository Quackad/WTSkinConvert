import os
import sqlite3
from tkinter import Tk, Label, Button, filedialog, StringVar, Frame
from tkinter import ttk
from PIL import Image, ImageTk

# Connect to SQLite database
conn = sqlite3.connect('CDKData.db')
cursor = conn.cursor()

# Initialize main application window
root = Tk()
root.title("Skin Management Tool")
root.geometry("800x300")

selected_directory = StringVar()
selected_vehicle = StringVar(value="Select Vehicle")

# Dropdown menu variables
types = ["Air", "Ground"]
countries = ["USA", "Germany", "USSR", "Great Britain", "Japan", "China", "Italy", "France", "Sweden", "Israel"]
vehicles = ["Select Vehicle"]

# Function to update vehicle list based on type and country
selected_type = StringVar(value="Select Type")
selected_country = StringVar(value="Select Country")

old_country = ""
old_display_name = ""

new_country = ""
new_display_name = ""

def update_vehicles(*args):
    print("update_vehicles called")
    selected_t = selected_type.get()
    selected_c = selected_country.get()
    if selected_t != "Select Type" and selected_c != "Select Country":
        cursor.execute("SELECT Display_Name FROM CDKData WHERE Type = ? AND Country = ? ORDER BY Display_Name", (selected_t, selected_c))
        vehicle_names = [row[0] for row in cursor.fetchall()]
        selected_vehicle.set("Select Vehicle")
        vehicle_menu['values'] = vehicle_names

# Function to select directory
def select_directory():
    print("select_directory called")
    directory = filedialog.askdirectory()
    selected_directory.set(directory)
    if directory:
        read_directory(directory)

# Function to read directory and match 'CDK_Name' from .blk file
def read_directory(directory):
    global old_country, old_display_name
    print("read_directory called")
    blk_file = None
    for filename in os.listdir(directory):
        if filename.endswith(".blk"):
            blk_file = filename
            break

    if blk_file:
        cdk_name = blk_file.split('.')[0]  # Extract CDK_Name from blk filename
        cdk_name_formatted = cdk_name.lower().replace('-', '_')
        print(f"Extracted and formatted CDK_Name: {cdk_name_formatted}")
        cursor.execute("SELECT Country, Display_Name FROM CDKData WHERE REPLACE(LOWER(CDK_Name), '-', '_') = ?", (cdk_name_formatted,))
        result = cursor.fetchone()
        if result:
            old_country, old_display_name = result
            print(f"Match found: Country={old_country}, Display_Name={old_display_name}")
            display_flag_and_name(old_country, old_display_name, old_flag_label, old_name_label)
        else:
            print(f"No match found for CDK_Name: {cdk_name}")
    else:
        print("No .blk file found in the directory.")

# Function to display country flag and name
def display_flag_and_name(country, display_name, flag_label, name_label):
    print(f"display_flag_and_name called with Country={country}, Display_Name={display_name}")
    flag_path = f"flags/{country.lower().replace(' ', '_')}.png"
    if os.path.exists(flag_path):
        img = Image.open(flag_path)
        img = img.resize((50, 30), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        flag_label.config(image=photo)
        flag_label.image = photo
    else:
        print(f"Flag not found for country: {country}")
        flag_label.config(image='')
        flag_label.image = None
    name_label.config(text=display_name)

# Function to replace 'CDK_Name' in .blk files and other matching files
def replace_cdk_name():
    global new_country, new_display_name
    print("replace_cdk_name called")
    blk_file = None
    directory = selected_directory.get()
    for filename in os.listdir(directory):
        if filename.endswith(".blk"):
            blk_file = filename
            break

    if blk_file:
        old_cdk_name = blk_file.split('.')[0]  # Extract CDK_Name from blk filename
        old_cdk_name_formatted = old_cdk_name.lower().replace('-', '_')
        print(f"Old CDK_Name formatted: {old_cdk_name_formatted}")
        
        # Get the new CDK_Name from the selected vehicle
        new_display_name = selected_vehicle.get()
        cursor.execute("SELECT CDK_Name, Country FROM CDKData WHERE Display_Name = ?", (new_display_name,))
        result = cursor.fetchone()

        if result:
            new_cdk_name, new_country = result
            new_cdk_name_formatted = new_cdk_name.lower().replace('-', '_')
            print(f"New CDK_Name: {new_cdk_name}")

            # Replace in text-based files (like .blk)
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        # Replace content in text-based files
                        if file.endswith((".blk", ".txt", ".ini")):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            # Replace all occurrences of old CDK name with the new one
                            content = content.replace(old_cdk_name, new_cdk_name).replace(old_cdk_name_formatted, new_cdk_name_formatted)
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            print(f"Replaced CDK_Name in {file_path}")
                        # Rename files
                        if old_cdk_name in file or old_cdk_name_formatted in file:
                            new_file_name = file.replace(old_cdk_name, new_cdk_name).replace(old_cdk_name_formatted, new_cdk_name_formatted)
                            new_file_path = os.path.join(root, new_file_name)
                            os.rename(file_path, new_file_path)
                            print(f"Renamed file {file} to {new_file_name}")
                    except UnicodeDecodeError:
                        print(f"Could not read {file_path} due to encoding issues.")
            # Display updated flag and name
            display_flag_and_name(new_country, new_display_name, new_flag_label, new_name_label)
        else:
            print("No matching vehicle found in the database for replacement.")
    else:
        print("No .blk file found in the directory.")

# UI Elements in a row at the top
options_frame = Frame(root)
options_frame.pack(pady=10)

Label(options_frame, text="Skin Directory:").grid(row=0, column=0, padx=5)
Button(options_frame, text="Browse", command=select_directory).grid(row=0, column=1, padx=5)

Label(options_frame, text="New Vehicle:").grid(row=1, column=0, padx=5)
Label(options_frame, text="Select Type:").grid(row=1, column=1, padx=5)
type_menu = ttk.Combobox(options_frame, textvariable=selected_type, values=types, state="readonly")
type_menu.grid(row=1, column=2, padx=5)
selected_type.trace("w", update_vehicles)

Label(options_frame, text="Select Country:").grid(row=1, column=3, padx=5)
country_menu = ttk.Combobox(options_frame, textvariable=selected_country, values=countries, state="readonly")
country_menu.grid(row=1, column=4, padx=5)
selected_country.trace("w", update_vehicles)

Label(options_frame, text="Select Vehicle:").grid(row=1, column=5, padx=5)
vehicle_menu = ttk.Combobox(options_frame, textvariable=selected_vehicle, values=vehicles, state="readonly")
vehicle_menu.grid(row=1, column=6, padx=5)

Button(options_frame, text="Replace CDK_Name", command=replace_cdk_name).grid(row=1, column=7, padx=5)

# Display old and new vehicle information with flags
display_frame = Frame(root)
display_frame.pack(pady=20)

old_flag_label = Label(display_frame)
old_flag_label.grid(row=0, column=0, padx=10)
old_name_label = Label(display_frame, text="")
old_name_label.grid(row=0, column=1, padx=10)

arrow_label = Label(display_frame, text="->")
arrow_label.grid(row=0, column=2, padx=10)

new_flag_label = Label(display_frame)
new_flag_label.grid(row=0, column=3, padx=10)
new_name_label = Label(display_frame, text="")
new_name_label.grid(row=0, column=4, padx=10)

root.mainloop()

# Close the database connection
conn.close()
