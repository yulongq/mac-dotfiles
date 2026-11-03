"""Exercise Rex close decisions with the Rex and AppKit boundaries stubbed."""

import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import unittest

from test_dotfiles import ROOT, run


SOURCE = ROOT / "home/dot_config/rex/actions/confirm_close.lua"


class RexCloseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nvim = run("asdf", "which", "nvim").stdout.strip()

    def setUp(self):
        workspace = tempfile.TemporaryDirectory(prefix="mac-dotfiles-rex-close-")
        self.addCleanup(workspace.cleanup)
        self.base = Path(workspace.name)
        self.environment = {"HOME": str(self.base), "TMPDIR": str(self.base),
                            "PATH": os.environ["PATH"]}

    def lua(self, assertions):
        script = self.base / "test.lua"
        script.write_text('''
local action, info, close_error, start_error, closed, started, killed
local handle = {
  running = function() return true end,
  kill = function() killed = true end,
}
rex = {
  action = function(value) action = value end,
  client = { queue = function() error("unexpected client close") end },
  block = { call = function() return info end },
  call = function(method, args)
    closed = {method = method, args = args}
    if close_error then return nil, close_error end
    return {}
  end,
  exec = { start = function(args, opts)
    started = {args = args, opts = opts}
    if start_error then return nil, start_error end
    return handle
  end },
}
''' + f'dofile({json.dumps(str(SOURCE))})\n' + '''
local ctx = {session_id = "fixture-session", block_id = "fixture-block"}
''' + assertions)
        # Neovim's declared LuaJIT runtime supplies Lua 5.1 semantics without
        # loading user configuration or requiring a running Rex server.
        result = subprocess.run(
            [self.nvim, "--headless", "-u", "NONE", "-i", "NONE", "-n", "-l", str(script)],
            env=self.environment, text=True, capture_output=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_idle_close_propagates_errors_and_preserves_target(self):
        self.lua('''
info = {foreground = {name = "zsh", argv0 = "-zsh"}}
action.run(ctx)
assert(closed.method == "block.close")
assert(closed.args.session_id == ctx.session_id and closed.args.block_id == ctx.block_id)
assert(not started)
close_error = "fixture close failure"
local ok, err = pcall(action.run, ctx)
assert(not ok and err:find(close_error, 1, true), "close failure was swallowed")
''')

    def test_confirmation_launch_failure_and_unknown_process(self):
        self.lua('''
start_error = "fixture launch failure"
local ok, err = pcall(action.run, ctx)
assert(not ok and err:find(start_error, 1, true), "launch failure was swallowed")
assert(not closed)
assert(started.args[6]:find("unavailable", 1, true), "unknown process was described as running")
assert(started.opts.detach == true)
''')

    def test_running_program_and_repeated_request_keep_one_confirmation(self):
        self.lua('''
info = {foreground = {name = "sh", argv0 = "sh"}}
action.run(ctx)
assert(not closed and started.args[6]:find("sh is still running", 1, true))
action.run(ctx)
assert(killed, "previous confirmation was not cancelled")
assert(started.args[8] == ctx.session_id and started.args[9] == ctx.block_id)
''')

    def javascript(self, scenario):
        body = re.search(r"local alert = \[\[\n(.*?)\n\]\]", SOURCE.read_text(), re.S).group(1)
        calls = self.base / "close-arguments"
        calls.unlink(missing_ok=True)
        command = self.base / "close"
        command.write_text("#!/bin/sh\n"
                           f"printf '%s\\0' \"$@\" > {shlex.quote(str(calls))}\n"
                           f"printf '%s' {shlex.quote(scenario.get('stderr', ''))} >&2\n"
                           f"exit {scenario.get('status', 0)}\n")
        command.chmod(0o755)
        if scenario.get("launch") is False:
            command.unlink()
        script = self.base / "test.js"
        script.write_text('''
ObjC.import("Foundation");
function run(argv) {
const scenario = JSON.parse(argv[0]);
const native = $;
const result = {alerts: [], cancelled: false, activated: false};
const app = {
  setActivationPolicy() {}, activateIgnoringOtherApps() {},
  performSelectorWithObjectAfterDelayInModes() {},
  isActive: scenario.active !== false,
};
function ui(value) { return native(value); }
ui.NSApplication = {sharedApplication: app};
ui.NSRunningApplication = {runningApplicationsWithBundleIdentifier() {
  return {firstObject: {icon: "fixture", activateWithOptions() { result.activated = true; }}};
}};
ui.NSUserDefaults = {alloc: {initWithSuiteName() {
  return {stringForKey() { return {js: null}; }};
}}};
ui.NSAlert = {alloc: {get init() {
  const alert = {addButtonWithTitle() {}};
  Object.defineProperty(alert, "runModal", {get() {
    result.alerts.push({title: alert.messageText, message: alert.informativeText});
    if (result.alerts.length > 1 && !result.cancelled) throw Error("stale confirmation timer");
    return scenario.response === undefined ? 1000 : scenario.response;
  }});
  return alert;
}}};
ui.NSObject = {cancelPreviousPerformRequestsWithTarget() {result.cancelled = true;}};
ui.NSAlertFirstButtonReturn = 1000;
ui.NSModalPanelRunLoopMode = "modal";
ui.NSApplicationActivationPolicyAccessory = 1;
for (const name of ["NSURL", "NSPipe", "NSString", "NSUTF8StringEncoding", "NSTask"]) ui[name] = native[name];
function invoke($) {
''' + body + '''
run(["Fixture is still running.", argv[1], "fixture-session", "fixture-block"]);
}
invoke(ui);
return JSON.stringify(result);
}
''')
        result = subprocess.run(["/usr/bin/osascript", "-l", "JavaScript", str(script), json.dumps(scenario), str(command)],
                                env=self.environment, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        actual = json.loads(result.stdout)
        actual["launched"] = calls.exists()
        actual["args"] = calls.read_bytes().decode().split("\0")[:-1] if calls.exists() else []
        return actual

    def test_confirmed_close_has_request_deadline_and_exact_target(self):
        actual = self.javascript({})
        self.assertEqual(actual["args"], ["--autostart=false", "--timeout=5s", "block", "close",
                                         "-s", "fixture-session", "fixture-block"])
        self.assertEqual(len(actual["alerts"]), 1)
        self.assertTrue(actual["activated"])

    def test_failed_close_reports_launch_stderr_or_exit_status(self):
        for scenario, message in (({"launch": False}, "could not be started"),
                                  ({"status": 1, "stderr": "fixture request timed out"}, "fixture request timed out"),
                                  ({"status": 7}, "status 7")):
            with self.subTest(scenario=scenario):
                actual = self.javascript(scenario)
                self.assertEqual(len(actual["alerts"]), 2)
                self.assertIn(message, actual["alerts"][1]["message"])

    def test_cancel_and_confirmation_timeout_never_launch_close(self):
        for response in (1001, -1001):
            with self.subTest(response=response):
                actual = self.javascript({"response": response, "active": False})
                self.assertFalse(actual["launched"])
                self.assertFalse(actual["activated"])


if __name__ == "__main__":
    unittest.main()
