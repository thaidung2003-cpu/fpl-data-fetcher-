import streamlit as st
import requests

st.title("Panna Data Diagnostic Tool")

st.write("Checking the peteowen1/panna repository...")

# 1. Check if the repo exists and is public
repo_url = "https://api.github.com/repos/peteowen1/panna"
repo_resp = requests.get(repo_url)

if repo_resp.status_code == 404:
    st.error("🚨 **Repository Not Found (404)**")
    st.write("This means `peteowen1/panna` is either deleted, misspelled, or **Private**.")
    st.write("If it is a private repository, you will need to generate a GitHub Personal Access Token (PAT) to download the data in Python.")
elif repo_resp.status_code == 200:
    st.success("✅ **Repository found and is Public!**")
    
    # 2. Check the releases to find the exact data tag
    releases_url = "https://api.github.com/repos/peteowen1/panna/releases"
    rel_resp = requests.get(releases_url)
    
    if rel_resp.status_code == 200:
        releases = rel_resp.json()
        if not releases:
            st.warning("No releases found in this repository. The data might be stored somewhere else.")
        else:
            st.write(f"Found {len(releases)} releases. Here are the most recent ones and their files:")
            
            for rel in releases[:3]:  # Check top 3 releases
                st.subheader(f"Tag: {rel.get('tag_name')} | Name: {rel.get('name')}")
                assets = rel.get('assets', [])
                if assets:
                    for asset in assets:
                        st.code(f"File: {asset.get('name')}\nDownload URL: {asset.get('browser_download_url')}")
                else:
                    st.write("No files attached to this release.")
    else:
        st.error(f"Failed to fetch releases. Status Code: {rel_resp.status_code}")
else:
    st.error(f"Unexpected response: {repo_resp.status_code}")
    st.write(repo_resp.text)
