#!/usr/bin/env bash
# Create a scoped baseline object for the review fix workflow.
# Input is a NUL-delimited file of repo-relative paths the fixer may touch.
# Stdout prints the baseline commit id. Stderr prints refusal, ambiguity, or usage errors.

set -euo pipefail

# shellcheck source=_lib.sh
source "$(dirname "$0")/_lib.sh"

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "${0##*/}: usage: ${0##*/} <fix-scope-file> [classified-ordinary-file]" >&2
  exit 2
fi

FIX_SCOPE_FILE="$1"
if [ ! -f "$FIX_SCOPE_FILE" ]; then
  echo "${0##*/}: fix scope file does not exist" >&2
  exit 2
fi
# An empty scope would snapshot zero paths yet print a plausible baseline id;
# a later rollback against it would overwrite scope files with HEAD content.
if [ ! -s "$FIX_SCOPE_FILE" ]; then
  echo "${0##*/}: empty fix scope file" >&2
  exit 2
fi

# Classifications from the review must also reach the snapshot's path check.
validate_path_file_nul "$FIX_SCOPE_FILE" "${2:-}"
REVIEW_ROOT=$(git rev-parse --show-toplevel)

TMP_INDEX=$(mktemp)
cleanup() { rm -f "$TMP_INDEX"; }
trap cleanup EXIT

GIT_INDEX_FILE="$TMP_INDEX" git -C "$REVIEW_ROOT" read-tree HEAD
GIT_INDEX_FILE="$TMP_INDEX" git -C "$REVIEW_ROOT" --literal-pathspecs add \
  --pathspec-from-file=- \
  --pathspec-file-nul < "$FIX_SCOPE_FILE"
BASELINE_TREE=$(GIT_INDEX_FILE="$TMP_INDEX" git -C "$REVIEW_ROOT" write-tree)
BASELINE=$(git -C "$REVIEW_ROOT" commit-tree "$BASELINE_TREE" -p HEAD -m "review-fix-baseline")
printf '%s\n' "$BASELINE"
