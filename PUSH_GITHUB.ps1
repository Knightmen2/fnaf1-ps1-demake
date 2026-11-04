# Run AFTER: gh auth login
cd $env:USERPROFILE\Downloads\fnaf1-ps1-github-clean
gh repo create fnaf1-ps1-demake --public --source=. --remote=origin --push --description "FNAF 1 PS1 demake (PSn00bSDK) — open source"
gh repo view --web
