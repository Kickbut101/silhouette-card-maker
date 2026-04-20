import os
import shutil
import re
import click
from pathlib import Path

image_folders = ['front', 'double_sided']

@click.command()
@click.option('--dirs', default=image_folders, show_default=True, help='Relative folder paths under the game root. Provide multiple values or a single comma/semicolon-separated string.')
@click.option('--root', default='game', show_default=True, help='Root directory (default: game)')


def delete_files(dirs, root='game'):
    
    # Normalize incoming dirs:
    if (dirs is None) or (dirs == ""):
        image_folders = ['front', 'double_sided']
    elif isinstance(dirs, str):
        # accept comma/semicolon separated string or single folder name
        parts = re.split(r'[;,]', dirs)
        image_folders = [p.strip() for p in parts if p.strip()]
    elif isinstance(dirs, (list, tuple, set)):
        image_folders = list(dirs)
    else:
        raise TypeError('dirs must be None, a string, or an iterable of strings')

    i = 0

    for folder_name in image_folders:
        cleaned_path = subtract_root(folder_name, root)
        working_path = os.path.join(root, cleaned_path)

        if not os.path.exists(working_path):
            print(f'Skipping missing folder: {working_path}')
            continue

        for item in os.listdir(working_path):
            full_path = os.path.join(working_path, item)

            if os.path.basename(full_path) == 'EMPTY.md':
                continue

            if os.path.isfile(full_path):
                os.remove(full_path)
                print(f'Deleted file {full_path}')
                i += 1
            elif os.path.isdir(full_path):
                shutil.rmtree(full_path)
                print(f'Deleted directory {full_path}')
                i += 1

    print(f'Deleted {i} item{"s" if i != 1 else ""}')

def subtract_root(full_path, root_path):
    p = Path(full_path)
    r = Path(root_path)
    try:
        return str(p.relative_to(r))
    except ValueError:
        return os.path.relpath(str(p), str(r))

if __name__ == '__main__':

    #dirs= ['ashes\\grey\\front', 'ashes\\black\\front']
    #delete_files.callback(dirs=dirs, root='game')
    delete_files()