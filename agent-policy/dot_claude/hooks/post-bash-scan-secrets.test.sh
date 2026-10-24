#!/usr/bin/env bash
# Exercise the hook with synthetic output; never print the generated values.
set -u
HOOK="$(cd "$(dirname "$0")" && pwd)/executable_post-bash-scan-secrets.sh"
fixture=$(mktemp -d)
trap 'rm -rf "$fixture"' EXIT
PASS=0
FAIL=0

random() {
  head -c 1024 /dev/urandom | LC_ALL=C tr -dc 'A-Za-z0-9' | head -c "$1"
}

report() {
  if "$2"; then
    printf 'ok: %s\n' "$1"
    PASS=$((PASS + 1))
  else
    printf 'FAIL: %s\n' "$1"
    FAIL=$((FAIL + 1))
  fi
}

payload() {
  jq -nc --arg event "$1" --arg text "$2" --arg stderr "${3:-}" '
    {hook_event_name: $event, tool_name: "Bash"} +
    if $event == "PostToolUseFailure" then {error: $text}
    else {tool_response: {stdout: $text, stderr: $stderr}} end'
}

run_case() {
  local label="$1" expected="$2" event="$3" result status warn ok=false
  result=$(payload "$event" "$4" "${5:-}" | bash "$HOOK" 2>"$fixture/stderr")
  status=$?
  warn=$(printf '%s' "$result" | jq -r '.hookSpecificOutput.additionalContext // ""')
  if [[ $status == 0 ]]; then
    if [[ $expected == none && $result == '{}' ]]; then
      ok=true
    elif [[ $expected == warn && -n $warn && $warn != *"$SECRET"* ]] &&
      [[ $(printf '%s' "$result" | jq -r '.hookSpecificOutput.hookEventName') == "$event" ]] &&
      ! grep -Fq "$SECRET" "$fixture/stderr"; then
      ok=true
    fi
  fi
  report "$label" "$ok"
}

SECRET="ghp_$(random 36)"
run_case 'stdout vendor token' warn PostToolUse "token: $SECRET"
run_case 'stderr vendor token' warn PostToolUse done "token: $SECRET"
run_case 'failed command output' warn PostToolUseFailure "failure: $SECRET"
SECRET="glpat-$(random 20)"
run_case 'GitLab token without an assignment' warn PostToolUse "$SECRET"
SECRET=$(random 40)
run_case 'Authorization header' warn PostToolUse "> Authorization: Bearer $SECRET"
run_case 'Authorization without a scheme' warn PostToolUse "Authorization: $SECRET"
run_case 'escaped JSON header' warn PostToolUse "{\"request\": \"{\\\"Authorization\\\": \\\"Bearer $SECRET\\\"}\"}"
run_case 'standalone Bearer value' warn PostToolUse "Bearer $SECRET"
run_case 'X-Api-Key header' warn PostToolUse "X-Api-Key: $SECRET"
run_case 'X-Auth-Token header' warn PostToolUse "X-Auth-Token: $SECRET"
run_case 'named credential assignment' warn PostToolUse "SERVICE_TOKEN=$SECRET"
run_case 'quoted password assignment' warn PostToolUse "PASSWORD=\"$SECRET\""
SECRET=$(printf 'app:%s' "$(random 8)" | base64)
run_case 'short Basic credential' warn PostToolUse "> Authorization: Basic $SECRET"
SECRET=$(random 16)
run_case 'short Token credential' warn PostToolUse "Authorization: Token $SECRET"
SECRET=passpass
run_case 'low-complexity URL password' warn PostToolUse "postgres://app:$SECRET@db.internal/app"
SECRET="$(random 10):$(random 10)"
run_case 'URL password with a colon' warn PostToolUse "postgres://app:$SECRET@db.internal/app"
run_case 'header placeholders' none PostToolUse $'Authorization: Bearer undefined\nAuthorization: <YOUR_TOKEN_HERE>\nAuthorization: `Bearer ${apiToken}`'
run_case 'assignment placeholders' none PostToolUse $'SERVICE_TOKEN=${REAL_TOKEN}\nAPI_KEY={{ env.API_KEY }}\nexport TOKEN="$MY_TOKEN"'
run_case 'URL placeholders' none PostToolUse $'postgres://app:<password>@db.internal/app\npostgres://app:${DB_PASSWORD_1}@db.internal/app'
run_case 'clean command output' none PostToolUse 'GET /api/users 200 OK'
run_case 'clean command failure' none PostToolUseFailure 'Exit code 1: file not found'
run_case 'unrelated assignment' none PostToolUse "CHECKSUM=$(random 40)"

unscanned() {
  local label="$1" hook="$2" result status ok=false
  shift 2
  result=$(payload PostToolUse done | env "$@" /bin/bash "$hook" 2>/dev/null)
  status=$?
  [[ $status != 0 && -z $result ]] && ok=true
  report "$label" "$ok"
}

cp "$HOOK" "$fixture/scan.sh"
unscanned 'missing scanner configuration fails' "$fixture/scan.sh"
unscanned 'missing jq fails' "$HOOK" PATH=/bin
mkdir "$fixture/bin"
ln -s "$(command -v jq)" "$fixture/bin/jq"
ln -s /bin/cat "$fixture/bin/cat"
unscanned 'missing gitleaks fails' "$HOOK" "PATH=$fixture/bin"

printf '%d passed, %d failed\n' "$PASS" "$FAIL"
[[ $FAIL == 0 ]]
