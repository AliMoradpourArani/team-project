# Team Project Foundation Demo

This directory is the reference implementation for the shared member-project integration contract.

## Purpose

The demo proves that a reviewed student project can be discovered from `project.json`, validated against authoritative project metadata, displayed in the shared platform, and executed through the allowlisted local runner.

## Entry point

```text
main.py
```

## Run locally

Project execution is disabled by default. After the code has passed review and CI:

```bash
export PROJECT_RUNNER_ENABLED=true
```

Then run the application and open the project detail page:

```text
/projects/team-foundation
```

## Expected output

The script prints a short confirmation message and exits successfully.

## Security note

The manifest cannot provide arbitrary shell commands. The backend derives the Python command, uses `shell=False`, validates paths, and bounds runtime/output. This is still not a sandbox for untrusted code.
