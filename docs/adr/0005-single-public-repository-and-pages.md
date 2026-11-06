# ADR-0005: Single public repository with GitHub Pages

Date: 2026-11-05
Status: Accepted — explicit owner instruction; supersedes ADR-0001 visibility preference

## Context

GitHub rejected Pages on the private repository with HTTP 422 because the account plan does not support that configuration. The owner preferred simplicity and explicitly authorized a public OS repository instead of maintaining a second public dashboard repository.

## Decision

Use the single public markaraujo/toddy-os repository. Publish an allowlisted dashboard export using GitHub Pages and a main-branch Actions workflow. Do not create a second repository or cross-repository deployment credential. All dashboard updates follow validated Git changes.

## Consequences

Tracked content/history and the published dashboard are publicly visible. Keep secrets, personal runtime state and large build artifacts outside Git. The dashboard is a published snapshot, not a live process monitor. Technical licensing of original/reused components remains a separate work item.

## Source

GitHub Pages publishing documentation, consulted 2026-11-05: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
