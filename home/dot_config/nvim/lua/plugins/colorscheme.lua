-- https://www.lazyvim.org/plugins/colorscheme

return {
  {
    "gbprod/nord.nvim",
    lazy = false,
    priority = 1000,
    init = function()
      vim.opt.background = "light"
    end,
    opts = {
      on_colors = function()
        require("foxberry").on_colors()
      end,
      on_highlights = function(highlights)
        require("foxberry").on_highlights(highlights)
      end,
    },
  },
  { "nvim-lualine/lualine.nvim", opts = { options = { theme = "foxberry" } } },
  {
    "LazyVim/LazyVim",
    opts = {
      -- colorscheme = "gruvbox",
      colorscheme = "nord",
      -- colorscheme = "catppuccin-macchiato", -- catppuccin-latte, catppuccin-faappe, catppuccin-macchiato, catppuccin-mocha
    },
  },
}
