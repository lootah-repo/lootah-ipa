import requests
import zipfile
import plistlib
import os
import shutil

def download_and_extract(url, name="temp.ipa"):
    response = requests.get(url)
    open(name, 'wb').write(response.content)

    with zipfile.ZipFile(name, mode="r") as archive:
        for file_name in archive.namelist():
            if file_name.endswith(".app/Info.plist"):
                info_file = file_name

        with archive.open(info_file) as fp:
            return plistlib.load(fp)

def get_bundle_id_and_icon(url, name="temp.ipa", icon_folder="icons/"):
    pl = download_and_extract(url, name)

    bundle_id = pl.get("CFBundleIdentifier", "com.example.app")
    icon_path = ""

    if "CFBundleIconFiles" in pl:
        icon_path = os.path.join(os.path.dirname(info_file), pl["CFBundleIconFiles"][0])
    elif "CFBundleIcons" in pl:
        icon_prefix = pl["CFBundleIcons"]["CFBundlePrimaryIcon"]["CFBundleIconFiles"][0]
        for file_name in archive.namelist():
            if icon_prefix in file_name:
                icon_path = file_name

    if icon_path:
        try:
            icon_name = os.path.basename(icon_path)  # Extract the icon name from the path
            with archive.open(icon_path) as origin, open(icon_folder + bundle_id + "_" + icon_name, "wb") as dst:
                shutil.copyfileobj(origin, dst)
        except Exception as e:
            print(f"Error copying icon: {e}")

    return bundle_id
