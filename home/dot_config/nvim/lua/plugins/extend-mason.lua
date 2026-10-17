local ensure_installed = {
  "bash-language-server",
  "css-lsp",
  "docker-compose-language-service",
  "dockerfile-language-server",
  "erb-formatter",
  "erb-lint",
  "eslint-lsp",
  "flake8",
  "hadolint",
  "html-lsp",
  "json-lsp",
  "lua-language-server",
  "markdown-toc",
  "markdownlint",
  "markdownlint-cli2",
  "marksman",
  "phpactor",
  "prettier",
  "shellcheck",
  "shfmt",
  "sqlfluff",
  "stylua",
  "tailwindcss-language-server",
  "taplo",
  "typescript-language-server",
  "vim-language-server",
  "vue-language-server",
  "yaml-language-server",
}

local function dedupe(list)
  local seen = {}
  local out = {}
  for _, item in ipairs(list) do
    if not seen[item] then
      seen[item] = true
      out[#out + 1] = item
    end
  end
  return out
end

return {
  {
    "mason-org/mason.nvim",
    opts = function(_, opts)
      opts.ensure_installed = opts.ensure_installed or {}
      vim.list_extend(opts.ensure_installed, ensure_installed)
      opts.ensure_installed = dedupe(opts.ensure_installed)
    end,
  },
}
