from github import Github
import json
import argparse
import pandas as pd
import requests
import zipfile
import os
import shutil

def fetch_existing_data():
    if os.path.exists("bundleId.csv"):
        return pd.read_csv("bundleId.csv")
    return pd.DataFrame(columns=["name", "bundleId"])

def get_bundle_id_and_icon(ipa_file_url):
    # Download the IPA file
    response = requests.get(ipa_file_url)
    with open("temp.ipa", "wb") as ipa_file:
        ipa_file.write(response.content)

    # Extract bundle ID and other relevant information
    bundle_id = extract_bundle_id("temp.ipa")
    # Clean up temporary files if needed
    # os.remove("temp.ipa")

    return bundle_id

def extract_bundle_id(ipa_file_path):
    with zipfile.ZipFile(ipa_file_path, 'r') as ipa_zip:
        # You need to replace "Info.plist" with the actual path to the Info.plist file in your IPA
        with ipa_zip.open("Payload/YourApp.app/Info.plist") as plist_file:
            # Extract bundle ID from the Info.plist file
            # You need to replace "CFBundleIdentifier" with the actual key for bundle ID in your Info.plist
            # You might want to use a proper plist parser for this task
            bundle_id = "com.example.app"  # Replace this with your actual logic

    return bundle_id

def process_release(asset, repo_name, df, data):
    if not asset.name.endswith(".ipa"):
        return

    name = asset.name[:-4]
    date = asset.created_at.strftime("%Y-%m-%d")
    full_date = asset.created_at.strftime("%Y%m%d%H%M%S")

    try:
        app_name, version, tweaks = name.split("_", 2)
        tweaks, _ = tweaks.split("@", 1)
        if tweaks:
            tweaks = "Injected with " + tweaks[:-1].replace("_", " ")
    except:
        app_name = name
        version = "Unknown"
        tweaks = None

    bundle_id = df.loc[df["name"] == app_name, "bundleId"].values[0] if app_name in df["name"].values else get_bundle_id_and_icon(asset.browser_download_url)

    # Check if the app already exists in the data dictionary
    existing_app = next((app for app in data["apps"] if app["name"] == app_name), None)

    if existing_app:
        # Update only if the new version has a more recent release date
        existing_release_date = pd.to_datetime(existing_app["versionDate"], format="%Y-%m-%d", errors="coerce")
        new_release_date = pd.to_datetime(date, format="%Y-%m-%d", errors="coerce")

        if new_release_date > existing_release_date:
            existing_app.update({
                "version": version,
                "versionDate": date,
                "fullDate": full_date,
                "size": asset.size,
                "down": asset.browser_download_url,
                "downloadURL": asset.browser_download_url,
                "localizedDescription": tweaks,
            })
    else:
        # Add a new entry for the app
        data["apps"].append({
            "name": app_name,
            "realBundleID": bundle_id,
            "bundleID": bundle_id,
            "bundleIdentifier": bundle_id,
            "version": version,
            "versionDate": date,
            "fullDate": full_date,
            "size": asset.size,
            "down": asset.browser_download_url,
            "downloadURL": asset.browser_download_url,
            "developerName": "",
            "localizedDescription": tweaks,
            "icon": f"https://raw.githubusercontent.com/{repo_name}/main/icons/{bundle_id}.png",
            "iconURL": f"https://raw.githubusercontent.com/{repo_name}/main/icons/{bundle_id}.png"
        })

def main(token):
    out_file = "apps.json"
    clone_file = "index.html"

    existing_data = fetch_existing_data()

    # Clear apps
    data = {"apps": []}

    g = Github(token)
    repo_name = "lootah-repo/lootah-ipa"
    repo = g.get_repo(repo_name)
    releases = repo.get_releases()

    for release in releases:
        print(release.title)

        for asset in release.get_assets():
            process_release(asset, repo_name, existing_data, data)

    existing_data.to_csv("bundleId.csv", index=False)

    with open(out_file, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    shutil.copyfile(out_file, clone_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--token", help="Github token")
    args = parser.parse_args()
    token = args.token

    main(token)
