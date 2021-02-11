from pathlib import Path
import argparse
import random

from PIL import Image
import natsort

parser = argparse.ArgumentParser()
parser.add_argument("--img_folder", "-i", type=Path, required=True,
                    help="Path of folder containing images")
parser.add_argument("--label_folder", "-l", type=Path, required=False, default=None,
                    help="Path to folder containing labels. Ignore if it is same as img_folder")
parser.add_argument("--output_folder", "-o", type=Path, required=False, default=None,
                    help="Output folder to save train.txt and val.txt. Ignore if same folder as label_folder")
parser.add_argument("--val_percentage", "-v", type=float, required=True,
                    help="Percentage of images to use as validation. Can be 0")
parser.add_argument("--ignore_missing_labels", action="store_true", 
                    help="Ignore errors when there is no label for an image. E.g. Image has not bbox in it")
parser.add_argument("--overwrite_files", action="store_true",
                    help="Overwrittes train.txt and val.txt if they already exist")

def labelimg_to_txt(img_folder: Path,
                    val_percentage: float,
                    label_folder: Path=None,
                    output_folder: Path=None,
                    ignore_missing_labels: bool=False,
                    overwrite_files: bool=False
                    ) -> None:
    """Converts labelimg format into txt val and train files.

    Converts formats from labelimg yolo format into format like:
    image_path1 x1,y1,x2,y2,id x1,y1,x2,y2,id x1,y1,x2,y2,id ...

    Also chooses random set of val_percentage % images to create 
    the val set

    Caution: All images should have the same size

    Args:
        img_folder (str)
        label_folder (str)
        output_folder (str)
        val_percentage (float)
        ignore_missing_labels (bool)

    Output:
        train.txt and val.txt at output_folder
    """
    # Checks
    assert img_folder.is_dir()
    assert 0 <= val_percentage <= 1
    
    # Populate vars
    if label_folder is None: label_folder = img_folder
    if output_folder is None: output_folder = label_folder

    # Find imgs
    exts = ["jpg", "png", "jpeg"]
    exts += [el.upper() for el in exts]
    files = [img_folder.glob(f"*.{el}") for el in exts]
    files = [el for ext in files for el in ext]

    # Sort files
    key = natsort.natsort_keygen(lambda x: str(x))
    files.sort(key=key)

    # Get img size
    img = Image.open(str(files[0]))
    img_width, img_height = img.size

    train = []
    for img in files:
        # Load label file
        label_file = label_folder / img.with_suffix(".txt")
        if not label_file.is_file():
            if ignore_missing_labels:
                labels = ""
            else:
                raise Exception(f"File {lable_file} does not exists")
        else:
            with open(str(label_file), "r") as f:
                labels = f.readlines()
        
        # Populate each line of train.txt
        line = ""
        for label in labels:
            id, *coords = label.split()
            x, y, w, h = [float(el) for el in coords]

            x1 = int((x + w/2) * img_width)
            x2 = int((x - w/2) * img_width)
            y1 = int((y + h/2) * img_height)
            y2 = int((y - h/2) * img_height)

            if len(line) > 0:
                line += ","

            line += f"{x1},{y1},{x2},{y2},{id}"
            
        line += "\n"
        train.append(f"{label_file} {line}")

    # Create val file
    val_idx = random.choices(range(len(train)), k=int(val_percentage * len(train)))
    val = [train[id] for id in val_idx]

    # Update train file
    train = [train[id] for id in range(len(train)) if id not in val_idx]

    # Save files
    train_file = output_folder / "train.txt"
    val_file = output_folder / "val.txt"

    # Check if conflict
    if train_file.is_file() and not overwrite_files:
        raise Exception(f"{train_file} already exists")
    if val_file.is_file() and not overwrite_files:
        raise Exception(f"{val_file} already exists")
    
    # Saves files
    with open(str(train_file), "w") as f:
        f.writelines(train)
    with open(str(val_file), "w") as f:
        f.writelines(val)


if __name__ == "__main__":
    args = parser.parse_args()
    labelimg_to_txt(**dict(vars(args)))
