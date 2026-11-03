-- Rex can neither confirm nor undo closing a pane, which ends its program, so
-- this asks first unless the pane's program has exited or its login shell is
-- in the foreground. Remove it and its binding once Rex can do either; Rex
-- feedback post 1560649600577052752 tracks that.
local shells = { bash = true, fish = true, sh = true, zsh = true }

-- A system alert, because the Rex app can draw a floating layer invisible while
-- it keeps focus (Rex feedback post 1559241103117656144).
-- osascript has no activation policy, so without Accessory the alert opens
-- behind Rex and never gets focus. Focus does not reliably return to Rex when
-- osascript exits, so the alert hands focus back only while it still has it;
-- otherwise focus stays where it is. NSRunningApplication reports the
-- bundle icon, so the icon chosen under Rex's App Icon setting is loaded by the
-- preference and asset names Rex Beta uses for it. An unanswered alert gives up
-- after 20 seconds, so a forgotten one cannot close the pane long after its
-- program was asked about.
local alert = [[
ObjC.import("AppKit")
function run(argv) {
  const [message, cli, session, block] = argv
  const app = $.NSApplication.sharedApplication
  const rex = $.NSRunningApplication.runningApplicationsWithBundleIdentifier("com.superlogical.rex").firstObject
  const alert = $.NSAlert.alloc.init
  alert.messageText = "Close Pane?"
  alert.informativeText = message + " Closing the pane will end its program."
  const choice = $.NSUserDefaults.alloc.initWithSuiteName("com.superlogical.rex").stringForKey("Workspace.appIcon").js
  const chosen = choice && $.NSBundle.bundleWithURL(rex.bundleURL).imageForResource("PlainAppIcon" + choice[0].toUpperCase() + choice.slice(1) + "Beta")
  alert.icon = chosen && !chosen.isNil() ? chosen : rex.icon
  alert.addButtonWithTitle("Close")
  alert.addButtonWithTitle("Cancel")
  app.setActivationPolicy($.NSApplicationActivationPolicyAccessory)
  app.activateIgnoringOtherApps(true)
  app.performSelectorWithObjectAfterDelayInModes("abortModal", $(), 20, $([$.NSModalPanelRunLoopMode]))
  const response = alert.runModal
  $.NSObject.cancelPreviousPerformRequestsWithTarget(app)
  if (response == $.NSAlertFirstButtonReturn) {
    // Close by ID the pane the key was pressed in, which need not have focus by now.
    const close = $.NSTask.alloc.init
    close.executableURL = $.NSURL.fileURLWithPath(cli)
    close.arguments = $(["--autostart=false", "--timeout=5s", "block", "close", "-s", session, block])
    const stderr = $.NSPipe.pipe
    close.standardError = stderr
    let failure
    if (close.launchAndReturnError(null)) {
      const output = stderr.fileHandleForReading.readDataToEndOfFile
      close.waitUntilExit
      if (close.terminationStatus != 0) {
        failure = $.NSString.alloc.initWithDataEncoding(output, $.NSUTF8StringEncoding).js || "Rex exited with status " + close.terminationStatus + "."
      }
    } else {
      failure = "The Rex command could not be started."
    }
    if (failure) {
      const error = $.NSAlert.alloc.init
      error.messageText = "Could Not Close Pane"
      error.informativeText = failure
      error.icon = alert.icon
      error.addButtonWithTitle("OK")
      error.runModal
    }
  }
  if (app.isActive) rex.activateWithOptions(0)
}
]]

-- Commands the server starts get only the system PATH, so name the installed
-- server's CLI.
local cli = os.getenv("HOME") .. "/Library/Application Support/com.superlogical.rex/RexServer/Versions/Current/Rex Server.app/Contents/MacOS/rex"

-- Cmd+W ends an open alert first, so at most one alert is open and it asks
-- about the latest request.
local pending

rex.action{
  name = "confirm_close",
  title = "Close, Confirming a Running Program",
  run = function(ctx)
    if pending and pending:running() then pending:kill() end
    if not ctx.block_id then
      rex.client.queue("client.close")
      return
    end
    local info = rex.block.call("com.superlogical.terminal", "process", { block_id = ctx.block_id })
    local foreground = info and info.foreground
    -- A shell running a command, such as `sh -c` around a pipeline, also reports
    -- itself, so only a login shell, whose argv0 starts with "-", counts as idle.
    -- A failed lookup asks, because a wrong guess ends a running program.
    local idle = info and (info.last_exit or (foreground and shells[foreground.name] and (foreground.argv0 or ""):sub(1, 1) == "-"))
    if idle then
      assert(rex.call("block.close", { session_id = ctx.session_id, block_id = ctx.block_id }))
      return
    end
    local message = "The pane's program status is unavailable."
    if foreground then
      message = (foreground.script or foreground.argv0 or foreground.name):match("[^/]+$") .. " is still running."
    end
    -- The server runs a client's keys, actions, and focus changes one at a time
    -- (`rex api describe client.action`), so waiting here would hold the clicks
    -- the app sends during the alert until the pane is gone, and they would then
    -- fail. The alert therefore runs detached and closes the pane itself, and
    -- without a shell, so that killing its handle ends the alert.
    pending = assert(rex.exec.start({
      "osascript", "-l", "JavaScript", "-e", alert, message, cli, ctx.session_id, ctx.block_id,
    }, { detach = true }))
  end,
}
