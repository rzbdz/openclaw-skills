---
name: junzhong-skills-manager
description: Install, update, and manage skills from Junzhong's personal skills repository (git@github.com:rzbdz/openclaw-skills.git). Use when you need to install new skills, update existing skills, or manage skill lifecycle from the upstream repository. Supports soft-linking for automatic updates on git pulls.
---

# Junzhong Skills Manager

This skill provides a workflow for installing, updating, and managing skills from Junzhong's personal repository.

## Quick Start

### Install a Skill from the Repository

```bash
# Skills are already soft-linked to ~/.openclaw/openclaw-skills/skills
# Simply use the skill directly from your workspace

# For Iris: ~/.openclaw/workspace/skills/<skill-name>
# For Alex: ~/.openclaw/workspace/agents/alex/skills/<skill-name>
```

### Update All Skills

```bash
# Pull latest changes from the repository
cd ~/.openclaw/openclaw-skills && git pull origin main

# All soft-linked skills automatically reflect the latest version
```

## Workflow

### 1. Repository Structure

Central repository location: `~/.openclaw/openclaw-skills/`

```
~/.openclaw/openclaw-skills/
├── skills/
│   ├── junzhong-skills-manager/
│   ├── remote-preview/
│   └── ...
└── .git/
```

### 2. Workspace Integration

Each agent's workspace has a soft link to the skills directory:

```
Iris workspace:
~/.openclaw/workspace/skills → ~/.openclaw/openclaw-skills/skills

Alex workspace:
~/.openclaw/workspace/agents/alex/skills → ~/.openclaw/openclaw-skills/skills
```

### 3. Update Skills

To get the latest versions of all skills:

```bash
cd ~/.openclaw/openclaw-skills
git pull origin main
```

All soft-linked skills in both workspaces automatically reflect the latest changes.

### 4. Verify Installation

Check that skills are properly installed:

```bash
# List available skills
ls -la ~/.openclaw/workspace/skills/

# Verify soft links
file ~/.openclaw/workspace/skills/<skill-name>

# Check SKILL.md exists
cat ~/.openclaw/workspace/skills/<skill-name>/SKILL.md
```

## Directory Structure

```
~/.openclaw/openclaw-skills/          # Central repository (git clone)
├── skills/
│   ├── junzhong-skills-manager/
│   ├── remote-preview/
│   └── ...
└── .git/

~/.openclaw/workspace/skills/         # Iris workspace (soft link)
└── → ~/.openclaw/openclaw-skills/skills

~/.openclaw/workspace/agents/alex/skills/  # Alex workspace (soft link)
└── → ~/.openclaw/openclaw-skills/skills
```

## Key Benefits

- **Single Source of Truth**: All skills live in one repository
- **Automatic Updates**: Pull once, all soft-linked skills update
- **No Duplication**: Soft links avoid redundant copies
- **Easy Management**: Simple git workflow for version control
- **Scalability**: Add new skills without manual copying
- **Agent Isolation**: Each agent can work with the same skills independently

## Troubleshooting

### Soft Link Not Working

```bash
# Verify the link target exists
readlink ~/.openclaw/workspace/skills

# Recreate the link if broken
rm ~/.openclaw/workspace/skills
ln -s ~/.openclaw/openclaw-skills/skills ~/.openclaw/workspace/skills
```

### Repository Not Found

```bash
# Verify the repository URL
cd ~/.openclaw/openclaw-skills
git remote -v

# Update if needed
git remote set-url origin https://github.com/rzbdz/openclaw-skills.git
```

### Pull Fails

```bash
# Check git status
cd ~/.openclaw/openclaw-skills
git status

# Stash local changes if needed
git stash

# Try pull again
git pull origin main
```
