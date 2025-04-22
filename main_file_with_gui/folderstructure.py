import os

def print_structure(root_dir, exclude_folder, indent=""):
    for item in sorted(os.listdir(root_dir)):
        path = os.path.join(root_dir, item)
        if os.path.isdir(path):
            if item == exclude_folder:
                continue
            print(f"{indent}📁 {item}")
            print_structure(path, exclude_folder, indent + "    ")
        else:
            print(f"{indent}📄 {item}")

# Example usage:
root_directory = r"C:\Users\Piyush\ML_miniproject\gui"
exclude = "venv"  # Replace with the folder you want to exclude
print_structure(root_directory, exclude)
