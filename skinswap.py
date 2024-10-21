import os
import sqlite3
from tkinter import Tk, Label, Button, filedialog, StringVar, OptionMenu
from tkinter import ttk
from PIL import Image, ImageTk

conn = sqlite3.connect('CDKData.db')
cursor = conn.cursor()

root = Tk()
root.title("Skin Management Tool")
root.geometry("800x600")

selected_directory = StringVar()
selected_vehicle = StringVar(value="Select Vehicle")

types = ["Air", "Ground"]
countries = ["USA", "Germany", "USSR", "Great Britain", "Japan", "China", "Italy", "France", "Sweden", "Israel"]
vehicles = ["Select Vehicle"]

selected_type = StringVar(value="Select Type")
selected_country = StringVar(value="Select Country")

def update_vehicles(*args):
    print("update_vehicles called")
    selected_t = selected_type.get()
    selected_c = selected_country.get()
    if selected_t != "Select Type" and selected_c != "Select Country":
        cursor.execute("SELECT Display_Name FROM CDKData WHERE Type = ? AND Country = ? ORDER BY Display_Name", (selected_t, selected_c))
        vehicle_names = [row[0] for row in cursor.fetchall()]
        vehicle_menu['menu'].delete(0, 'end')
        for name in vehicle_names:
            vehicle_menu['menu'].add_command(label=name, command=lambda value=name: selected_vehicle.set(value))

def select_directory():
    print("select_directory called")
    directory = filedialog.askdirectory()
    selected_directory.set(directory)
    if directory:
        read_directory(directory)

def read_directory(directory):
    print("read_directory called")
    blk_file = None
    for filename in os.listdir(directory):
        if filename.endswith(".blk"):
            blk_file = filename
            break

    if blk_file:
        cdk_name = blk_file.split('.')[0] 
        cdk_name_formatted = cdk_name.lower().replace('-', '_')
        print(f"Extracted and formatted CDK_Name: {cdk_name_formatted}")
        cursor.execute("SELECT Country, Display_Name FROM CDKData WHERE REPLACE(LOWER(CDK_Name), '-', '_') = ?", (cdk_name_formatted,))
        result = cursor.fetchone()
        if result:
            country, display_name = result
            print(f"Match found: Country={country}, Display_Name={display_name}")
            display_flag_and_name(country, display_name)
        else:
            print(f"No match found for CDK_Name: {cdk_name}")
    else:
        print("No .blk file found in the directory.")

def display_flag_and_name(country, display_name):
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

def replace_cdk_name():
    print("replace_cdk_name called")
    blk_file = None
    directory = selected_directory.get()
    for filename in os.listdir(directory):
        if filename.endswith(".blk"):
            blk_file = filename
            break

    if blk_file:
        old_cdk_name = blk_file.split('.')[0]  
        old_cdk_name_formatted = old_cdk_name.lower().replace('-', '_')
        print(f"Old CDK_Name formatted: {old_cdk_name_formatted}")
        
        # Get the new CDK_Name from the selected vehicle
        new_display_name = selected_vehicle.get()
        cursor.execute("SELECT CDK_Name FROM CDKData WHERE Display_Name = ?", (new_display_name,))
        result = cursor.fetchone()

        if result:
            new_cdk_name = result[0]
            new_cdk_name_formatted = new_cdk_name.lower().replace('-', '_')
            print(f"New CDK_Name: {new_cdk_name}")

            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if file.endswith((".blk", ".txt", ".ini")):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            content = content.replace(old_cdk_name, new_cdk_name).replace(old_cdk_name_formatted, new_cdk_name_formatted)
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            print(f"Replaced CDK_Name in {file_path}")
                        if old_cdk_name in file or old_cdk_name_formatted in file:
                            new_file_name = file.replace(old_cdk_name, new_cdk_name).replace(old_cdk_name_formatted, new_cdk_name_formatted)
                            new_file_path = os.path.join(root, new_file_name)
                            os.rename(file_path, new_file_path)
                            print(f"Renamed file {file} to {new_file_name}")
                    except UnicodeDecodeError:
                        print(f"Could not read {file_path} due to encoding issues.")
        else:
            print("No matching vehicle found in the database for replacement.")
    else:
        print("No .blk file found in the directory.")


# UI Elements
Label(root, text="Select Directory:").pack()
Button(root, text="Browse", command=select_directory).pack()

flag_label = Label(root)
flag_label.pack()
name_label = Label(root, text="")
name_label.pack()

Label(root, text="Select Type:").pack()
type_menu = OptionMenu(root, selected_type, *types)
type_menu.pack()
selected_type.trace("w", update_vehicles)

Label(root, text="Select Country:").pack()
country_menu = OptionMenu(root, selected_country, *countries)
country_menu.pack()
selected_country.trace("w", update_vehicles)

Label(root, text="Select Vehicle:").pack()
vehicle_menu = OptionMenu(root, selected_vehicle, *vehicles)
vehicle_menu.pack()

Button(root, text="Replace CDK_Name", command=replace_cdk_name).pack()

root.mainloop()

conn.close()
