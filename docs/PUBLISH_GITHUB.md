# Publishing BoostDeck CDS to GitHub

This release is a **source-build kit**, not a tested binary release. Complete `RELEASE_CHECKLIST.md` and review the security and licensing notes first. **Never upload** your `work/` directory, BMW framework libraries, local SSH config, backups, logs, vehicle/owner details or firmware images.

From **regular Mac Terminal** inside the extracted project folder:

```bash
# Inspect exactly what you're publishing
git init
git status --short
git add README.md LICENSE NOTICE.md CHANGELOG.md requirements.txt .gitignore \
  boostdeck.sh tools scripts tests docs assets .github
git status --short
git commit -m "Publish BoostDeck CDS source and installer"
```

Create a new GitHub repository in your account from the GitHub website, leaving "Add README" disabled. Then run the specific remote commands shown by GitHub, for example:

```bash
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/BoostDeck-CDS.git
git push -u origin main
```

Alternatively, if you already have the GitHub CLI installed and are authenticated:

```bash
gh repo create BoostDeck-CDS --public --source=. --remote=origin --push
```

If you publish a GitHub release, mark it **pre-release** and **source-build / experimental**, with a link to compatibility limitations. Do not promise that the package is ready for NBT Evo, 800×480 or every BMW. If you choose to publish downloadable `.tar` binaries someday, first check redistribution rights for linked code and dependencies and validate the exact target ABI in a controlled test setup.
