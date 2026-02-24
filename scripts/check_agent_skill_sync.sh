#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

extract_frontmatter_name() {
  local file="$1"
  awk '
    NR == 1 && $0 == "---" { in_frontmatter = 1; next }
    in_frontmatter && $0 == "---" { exit }
    in_frontmatter && $1 == "name:" {
      sub(/^name:[[:space:]]*/, "", $0)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", $0)
      gsub(/^"/, "", $0)
      gsub(/"$/, "", $0)
      gsub(/^'\''/, "", $0)
      gsub(/'\''$/, "", $0)
      print $0
      exit
    }
  ' "$file"
}

collect_claude_agents() {
  if [[ -d ".claude/agents" ]]; then
    find .claude/agents -maxdepth 1 -type f -name "*.md" -printf "%f\n" \
      | sed 's/\.md$//' \
      | sort -u
  fi
}

collect_codex_skills() {
  if [[ -d "skills" ]]; then
    find skills -mindepth 2 -maxdepth 2 -type f -name "SKILL.md" -printf "%h\n" \
      | xargs -r -n1 basename \
      | sort -u
  fi
}

validate_names() {
  local errors=0

  if [[ -d ".claude/agents" ]]; then
    while IFS= read -r file; do
      [[ -z "$file" ]] && continue
      local base name
      base="$(basename "$file" .md)"
      name="$(extract_frontmatter_name "$file" || true)"
      if [[ -z "$name" ]]; then
        echo "ERROR: Missing frontmatter name in $file"
        errors=1
      elif [[ "$name" != "$base" ]]; then
        echo "ERROR: Frontmatter name mismatch in $file (name: $name, file: $base)"
        errors=1
      fi
    done < <(find .claude/agents -maxdepth 1 -type f -name "*.md" | sort)
  fi

  if [[ -d "skills" ]]; then
    while IFS= read -r file; do
      [[ -z "$file" ]] && continue
      local dir name
      dir="$(basename "$(dirname "$file")")"
      name="$(extract_frontmatter_name "$file" || true)"
      if [[ -z "$name" ]]; then
        echo "ERROR: Missing frontmatter name in $file"
        errors=1
      elif [[ "$name" != "$dir" ]]; then
        echo "ERROR: Frontmatter name mismatch in $file (name: $name, dir: $dir)"
        errors=1
      fi
    done < <(find skills -mindepth 2 -maxdepth 2 -type f -name "SKILL.md" | sort)
  fi

  return "$errors"
}

tmp_claude="$(mktemp)"
tmp_skills="$(mktemp)"
trap 'rm -f "$tmp_claude" "$tmp_skills"' EXIT

collect_claude_agents > "$tmp_claude"
collect_codex_skills > "$tmp_skills"

if ! validate_names; then
  echo
  echo "Agent/skill metadata validation failed."
  exit 1
fi

missing_skills="$(comm -23 "$tmp_claude" "$tmp_skills" || true)"
missing_agents="$(comm -13 "$tmp_claude" "$tmp_skills" || true)"

if [[ -n "$missing_skills" || -n "$missing_agents" ]]; then
  echo "Agent/skill parity check failed."

  if [[ -n "$missing_skills" ]]; then
    echo
    echo "Missing Codex skills (expected skills/<name>/SKILL.md):"
    while IFS= read -r name; do
      [[ -z "$name" ]] && continue
      echo "  - $name"
    done <<< "$missing_skills"
  fi

  if [[ -n "$missing_agents" ]]; then
    echo
    echo "Missing Claude agents (expected .claude/agents/<name>.md):"
    while IFS= read -r name; do
      [[ -z "$name" ]] && continue
      echo "  - $name"
    done <<< "$missing_agents"
  fi

  echo
  echo "Fix parity, then rerun: bash scripts/check_agent_skill_sync.sh"
  exit 1
fi

echo "Agent/skill parity check passed."
