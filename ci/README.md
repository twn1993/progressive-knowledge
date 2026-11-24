# Continuous integration

`check.yml` is a GitHub Actions workflow that audits the bundled example at
tier L2 and also runs the minimal checker.

It lives here rather than in `.github/workflows/` because pushing a workflow
file requires a token with the `workflow` scope. To enable it:

```bash
gh auth refresh -h github.com -s workflow
mkdir -p .github/workflows
git mv ci/check.yml .github/workflows/check.yml
git commit -m "Enable CI" && git push
```

Or paste the file into the repository's Actions tab in the GitHub UI.
