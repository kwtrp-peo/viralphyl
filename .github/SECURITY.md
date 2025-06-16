# 🔐 Security Policy

## 🔑 Secrets Used in This Repo

### **1️⃣ `ORG_GITHUB_PAT`**  
- This is a GitHub Actions secret used for automated releases via semantic-release.  
- It wraps `GITHUB_TOKEN`, which is managed by GitHub and **expires on Fri, Sep 5 2025**.

## 🔍 How to Rotate Secrets  
If any secret expires or needs updating:  
1. Generate a new token from **GitHub → Settings → Developer Settings → Personal access tokens (classic)**.
2. Update the secret in **GitHub → Settings → Secrets → Actions**.  
3. The next workflow run will automatically use the new credentials.  

## 🛠 Reporting Security Issues  
If you find a security vulnerability in this repo, please [open a security advisory](https://github.com/samordil/semantic-release/security/advisories).
