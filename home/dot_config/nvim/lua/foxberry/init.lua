-- Foxberry for gbprod/nord.nvim, which only ships a dark variant.
-- Active when 'background' is light; with a dark background nord.nvim stays as is.
-- Setup: see the Neovim section in README.md.
-- Part of Foxberry, a light Nord theme. MIT license; see LICENSE and THIRD_PARTY_NOTICES.md.

local M = {}

M.FG = {
  ["#8FBCBB"] = "#36816F", -- nord7
  ["#88C0D0"] = "#287F92", -- nord8
  ["#81A1C1"] = "#5374B3", -- nord9
  ["#5E81AC"] = "#3F79A8", -- nord10
  ["#BF616A"] = "#BE525A", -- nord11
  ["#D08770"] = "#B15E37", -- nord12
  ["#EBCB8B"] = "#967044", -- nord13
  ["#A3BE8C"] = "#4E8044", -- nord14
  ["#B48EAD"] = "#986393", -- nord15
  ["#D8DEE9"] = "#3B4252",
  ["#E5E9F0"] = "#3B4252",
  ["#ECEFF4"] = "#2E3440",
  ["#BFC5D2"] = "#3B4252", -- markdown text
  ["#616E88"] = "#6A7488", -- comments
  ["#707D96"] = "#6A7488",
  ["#4C566A"] = "#8E97A8", -- line numbers, dimmed
  ["#434C5E"] = "#C9D0DC", -- indent guides
  ["#3B4252"] = "#C9D0DC",
  ["#2E3440"] = "#ECEFF4", -- text in the background color (e.g. ~ past the end of the buffer)
}

M.BG = {
  ["#2E3440"] = "#ECEFF4",
  ["#3B4252"] = "#E5E9F0",
  ["#434C5E"] = "#D8DEE9",
  ["#4C566A"] = "#C9D0DC",
  ["#D8DEE9"] = "#C9D0DC",
  ["#E5E9F0"] = "#C9D0DC",
  ["#ECEFF4"] = "#4C566A",
}

-- Nord accents as backgrounds: the pastel stays, text on it is dark
local ACCENTS = {}
for _, h in ipairs({ "#8FBCBB", "#88C0D0", "#81A1C1", "#5E81AC", "#BF616A", "#D08770", "#EBCB8B", "#A3BE8C", "#B48EAD" }) do
  ACCENTS[h] = true
end
local POLAR = { ["#2E3440"] = true, ["#3B4252"] = true, ["#434C5E"] = true, ["#4C566A"] = true }
local BADGE_FG = "#2E3440"

local function norm(c)
  return type(c) == "string" and c:sub(1, 1) == "#" and c:upper() or nil
end

function M.is_light()
  return vim.o.background == "light"
end

-- Text color for the current background (for your own highlight groups)
function M.fg(c)
  if not M.is_light() then
    return c
  end
  return M.FG[norm(c)] or c
end

local function convert(hl)
  if hl.link then
    return hl
  end
  local fg, bg = norm(hl.fg), norm(hl.bg)
  local out = vim.deepcopy(hl)
  if hl.reverse then
    -- reverse: fg is drawn as the background (stays pastel), bg as the text
    if fg then
      out.fg = M.BG[fg] or fg
    end
    if bg then
      out.bg = POLAR[bg] and BADGE_FG or (M.FG[bg] or bg)
    elseif fg and ACCENTS[fg] then
      -- without bg the text becomes the terminal background, i.e. light on pastel
      out.bg = BADGE_FG
    end
  else
    if fg then
      out.fg = (bg and ACCENTS[bg] and POLAR[fg]) and BADGE_FG or (M.FG[fg] or fg)
    end
    if bg then
      out.bg = M.BG[bg] or bg
    end
  end
  local sp = norm(hl.sp)
  if sp then
    out.sp = M.FG[sp] or sp
  end
  return out
end

-- on_colors: called before the groups are built. utils.darken blends a color with
-- #2E3440 (e.g. diagnostic backgrounds); here it has to blend with #ECEFF4.
local orig_darken
function M.on_colors()
  local u = require("nord.utils")
  orig_darken = orig_darken or u.darken
  if M.is_light() then
    u.darken = function(hex, amount, bg)
      return u.blend(hex, bg or "#ECEFF4", amount)
    end
  else
    u.darken = orig_darken
  end
end

-- :terminal palette, the same as Ghostty Foxberry
local TERM = {
  "#3B4252", "#BE525A", "#4E8044", "#967044", "#5374B3", "#986393", "#287F92", "#6A7488",
  "#4C566A", "#DA656D", "#619756", "#AD8455", "#658ACD", "#B077AB", "#489784", "#8E97A8",
}

function M.on_highlights(highlights)
  if not M.is_light() then
    return
  end
  for group, hl in pairs(highlights) do
    highlights[group] = convert(hl)
  end
  for i, c in ipairs(TERM) do
    vim.g["terminal_color_" .. (i - 1)] = c
  end
end

-- lualine: the same tints as the Starship segments, dark text
function M.lualine_theme()
  if not M.is_light() then
    return require("lualine.themes.nord")
  end
  -- the terminal background is #E5E9F0, so sections are one step darker to keep the whole bar visible
  local b = { fg = "#3B4252", bg = "#C9D0DC" }
  local c = { fg = "#4C566A", bg = "#D8DEE9" }
  local function mode(bg, fg)
    return { a = { fg = fg or BADGE_FG, bg = bg, gui = "bold" }, b = b, c = c }
  end
  return {
    normal = mode("#ACD3DE"),
    -- insert: a white nord4 badge in dark Nord; here its mirror, a dark one (grey #C9D0DC blended into section b)
    insert = mode("#4C566A", "#ECEFF4"),
    -- visual: foxberry (nord7 in dark Nord, but its pastel #B6D3D2 was almost equal to normal #ACD3DE)
    visual = mode("#DEC0CC"),
    replace = mode("#E5C4A1"),
    command = mode("#CAB0C6"),
    inactive = {
      a = { fg = "#6A7488", bg = "#D8DEE9" },
      b = { fg = "#6A7488", bg = "#D8DEE9" },
      c = { fg = "#6A7488", bg = "#D8DEE9" },
    },
  }
end

return M
