return {
  "avante-corp/avante.nvim",
  event = "VeryLazy",
  version = false,
  -- macOS 27's linker emits dylibs that fail dyld's LINKEDIT alignment check.
  build = vim.fn.has("mac") == 1
      and [[
SDKROOT="$(xcrun --sdk macosx26.5 --show-sdk-path)" \
RUSTFLAGS="-C link-arg=-undefined -C link-arg=dynamic_lookup -C linker-flavor=ld64.lld -C linker=$(rustc --print target-libdir)/../bin/rust-lld" \
make
]]
    or "make",
  opts = function()
    -- ACP must inherit the CLI's environment and use the existing Codex installation.
    local env = vim.fn.environ()
    env.CODEX_PATH = vim.fn.exepath("codex")

    return {
      provider = "codex",
      acp_providers = {
        codex = {
          command = "codex-acp",
          env = env,
        },
      },
      behaviour = {
        auto_approve_tool_permissions = false,
      },
      prompt_logger = { enabled = false },
      mappings = { ask = "<leader>av" },
      selector = { provider = "snacks" },
    }
  end,
  dependencies = {
    "nvim-lua/plenary.nvim",
    "MunifTanjim/nui.nvim",
    {
      "MeanderingProgrammer/render-markdown.nvim",
      opts_extend = { "file_types" },
      opts = { file_types = { "markdown", "Avante" } },
      ft = { "markdown", "Avante" },
    },
  },
}
