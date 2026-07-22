-- Rebalance pipe-table columns after translation expands Russian text.

local function text_length(value)
  local length = utf8.len(value)
  return length or #value
end

local function add_break_after_delimiter(element)
  if not element.text:find("[/%-]") then
    return nil
  end

  local inlines = pandoc.Inlines({})
  local start = 1
  while true do
    local delimiter = element.text:find("[/%-]", start)
    if not delimiter then
      if start <= #element.text then
        inlines:insert(pandoc.Str(element.text:sub(start)))
      end
      break
    end

    local character = element.text:sub(delimiter, delimiter)
    inlines:insert(pandoc.Str(element.text:sub(start, delimiter)))
    inlines:insert(pandoc.RawInline("latex", "\\allowbreak{}"))
    if character == "-" then
      inlines:insert(pandoc.RawInline("latex", "\\hspace{0pt}"))
    end
    start = delimiter + 1
  end

  return inlines
end

local function prepare_cell_for_latex(cell)
  cell.contents = cell.contents:walk({ Str = add_break_after_delimiter })
  for _, block in ipairs(cell.contents) do
    if block.t == "Plain" or block.t == "Para" then
      block.content:insert(1, pandoc.RawInline("latex", "\\hspace{0pt}"))
      break
    end
  end
end

local function observe_cell(stats, column, cell)
  local text = pandoc.utils.stringify(cell.contents)
  local compact = text:gsub("%s+", "")
  local span = cell.col_span or 1
  local apportioned_length = text_length(compact) / span

  for offset = 0, span - 1 do
    local target = stats[column + offset]
    if target then
      target.total_chars = target.total_chars + apportioned_length
      for token in text:gmatch("%S+") do
        target.max_token = math.max(target.max_token, text_length(token))
      end
      for token in text:gmatch("[A-Za-z0-9_+]+") do
        target.max_rigid_ascii = math.max(target.max_rigid_ascii, #token)
      end
    end
  end

  if FORMAT:match("latex") then
    prepare_cell_for_latex(cell)
  end
end

local function observe_row(stats, row)
  local column = 1
  for _, cell in ipairs(row.cells) do
    observe_cell(stats, column, cell)
    column = column + (cell.col_span or 1)
  end
end

local function observe_rows(stats, rows)
  for _, row in ipairs(rows) do
    observe_row(stats, row)
  end
end

local function normalize_scores(scores, total_score, minimum_widths)
  local widths = {}
  local active = {}
  local remaining_width = 1
  local remaining_score = total_score

  for index = 1, #scores do
    active[index] = true
  end

  while true do
    local fixed_column = false
    for index, score in ipairs(scores) do
      local minimum_width = minimum_widths[index]
      if active[index] and remaining_width * score / remaining_score < minimum_width then
        widths[index] = minimum_width
        active[index] = false
        remaining_width = remaining_width - minimum_width
        remaining_score = remaining_score - score
        fixed_column = true
      end
    end
    if not fixed_column then
      break
    end
  end

  for index, score in ipairs(scores) do
    if active[index] then
      widths[index] = remaining_width * score / remaining_score
    end
  end

  return widths
end

function Table(element)
  local stats = {}
  for index = 1, #element.colspecs do
    stats[index] = { max_rigid_ascii = 0, max_token = 0, total_chars = 0 }
  end

  observe_rows(stats, element.head.rows)
  for _, body in ipairs(element.bodies) do
    observe_rows(stats, body.head)
    observe_rows(stats, body.body)
  end
  observe_rows(stats, element.foot.rows)

  local scores = {}
  local total_score = 0
  local minimum_widths = {}
  local base_minimum = math.min(0.14, 1 / #stats)
  local extra_minimum = 0
  for index, column in ipairs(stats) do
    local score = math.max(column.max_token, 4) + 0.7 * math.sqrt(column.total_chars)
    scores[index] = score
    total_score = total_score + score

    local minimum_width = base_minimum
    if #stats >= 5 then
      minimum_width = math.max(
        minimum_width,
        math.min(0.22, 0.019 * column.max_rigid_ascii)
      )
    end
    minimum_widths[index] = minimum_width
    extra_minimum = extra_minimum + minimum_width - base_minimum
  end

  local extra_capacity = 1 - base_minimum * #stats
  if extra_minimum > extra_capacity then
    local scale = extra_capacity / extra_minimum
    for index, minimum_width in ipairs(minimum_widths) do
      minimum_widths[index] = base_minimum + (minimum_width - base_minimum) * scale
    end
  end

  local widths = normalize_scores(scores, total_score, minimum_widths)
  for index, colspec in ipairs(element.colspecs) do
    element.colspecs[index] = { colspec[1], widths[index] }
  end

  return element
end
