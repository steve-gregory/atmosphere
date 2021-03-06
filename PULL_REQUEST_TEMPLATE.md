## Description

Please describe your pull request. If it fixes a bug or resolves a feature request, be sure to link to that issue. When linking to an issue, please use `refs #...` in the description of the pull request.

## Checklist before merging Pull Requests
- [ ] New test(s) included to reproduce the bug/verify the feature
- [ ] Documentation created/updated at [Example link to documentation](https://example.test/doc#new_section) to give context to the feature
- [ ] If creating/modifying DB models which will contain secrets or sensitive information, PR to [clank](https://github.com/cyverse/clank) updating sanitation queries in `roles/sanitary-sql-access/templates/sanitize-dump.sh.j2`
- [ ] Reviewed and approved by at least one other contributor.
- [ ] If necessary, include a snippet in CHANGELOG.md
- [ ] New variables supported in Clank
- [ ] New variables committed to secrets repos
