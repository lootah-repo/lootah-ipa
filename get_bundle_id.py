import requests
import zipfile
import plistlib
from github import Github
import pandas as pd
import shutil
import os

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
            with archive.open(icon_path) as origin, open(icon_folder + bundle_id + ".png", "wb") as dst:
                shutil.copyfileobj(origin, dst)
        except Exception as e:
            print(f"Error copying icon: {e}")

    return bundle_id

def generate_bundle_id_csv(token, repo_name="lootah-repo/lootah-ipa"):
    g = Github(token)
    repo = g.get_repo(repo_name)
    releases = repo.get_releases()

    df = pd.DataFrame(columns=["name", "bundleId"])

    for release in releases:
        print(release.title)
        for asset in release.get_assets():
            if not asset.name.endswith("ipa"):
                continue
            name = asset.name[:-4]
            print(asset.name)

            try:
                app_name = name.split("-", 1)[0]
            except Exception as e:
                print(f"Error parsing app name: {e}")
                app_name = name

            bundle_id = get_bundle_id_and_icon(asset.browser_download_url)

            # Check if the bundle identifier already exists in the DataFrame
            if not df[df["bundleId"] == bundle_id].empty:
                continue

            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        {
                            "name": [app_name],
                            "bundleId": [bundle_id]
                        }
                    )
                ],
                ignore_index=True
            )

    df.to_csv("bundleId.csv", index=False)

if __name__ == "__main__":
    generate_bundle_id_csv(None)
