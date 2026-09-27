-- Внутренние ссылки на рисунки и главы русского издания.
-- Ручная нумерация сохраняется, а подписи и упоминания получают PDF-ссылки.

local chapter = 0
local in_reference_answers = false

local figure_words = {
  'Рисунок', 'рисунок', 'рисунке', 'рисунка', 'рисунку', 'рисунком',
  'рисунки', 'рисунков', 'Рис.', 'рис.'
}
local chapter_words = {
  'Глава', 'Главы', 'глава', 'главы', 'главе', 'главу', 'главой', 'главах'
}

local function figure_label(n, m) return 'fig:' .. n .. '-' .. m end
local function chapter_label(n) return 'chap:' .. n end

local function is_ascii_alnum(byte)
  return (byte >= 48 and byte <= 57)
      or (byte >= 65 and byte <= 90)
      or (byte >= 97 and byte <= 122)
end

local function ok_suffix(text)
  if text == '' then return true end
  local byte = text:byte(1)
  return not (is_ascii_alnum(byte) or byte == 45)
end

local function split_keyword(text, words)
  for _, word in ipairs(words) do
    local prefix = text:match('^(.-)' .. word .. '$')
    if prefix then
      if prefix == '' or not is_ascii_alnum(prefix:byte(#prefix)) then
        return prefix, word
      end
    end
  end
  return nil, nil
end

return {
  {
    traverse = 'topdown',

    Header = function(element)
      if element.level == 1 then
        in_reference_answers = pandoc.utils.stringify(element.content)
            == 'Справочные ответы на вопросы для размышления'
      end
      if in_reference_answers and not element.classes:includes('unnumbered') then
        element.classes:insert('unnumbered')
      end
      if element.level == 1 and not element.classes:includes('unnumbered') then
        chapter = chapter + 1
        element.content:insert(pandoc.RawInline(
          'latex', '\\label{' .. chapter_label(chapter) .. '}'
        ))
      end
      return element
    end,

    Figure = function(element)
      local caption = pandoc.utils.stringify(element.caption.long)
      local n, m = caption:match('Рисунок%s*(%d+)%-(%d+)')
      if n and m then
        element.identifier = figure_label(n, m)
      end
      return element, false
    end,

    Image = function(element)
      local caption = pandoc.utils.stringify(element.caption)
      local n, m = caption:match('Рисунок%s*(%d+)%-(%d+)')
      if n and m and element.identifier == '' then
        element.identifier = figure_label(n, m)
      end
      return element, false
    end,

    Inlines = function(inlines)
      local output = pandoc.Inlines{}
      local index = 1
      local count = #inlines
      local changed = false

      while index <= count do
        local element = inlines[index]
        local linked = false
        if element.t == 'Str' and index + 2 <= count
            and inlines[index + 1].t == 'Space'
            and inlines[index + 2].t == 'Str' then
          local prefix, keyword = split_keyword(element.text, figure_words)
          local kind = 'figure'
          if not prefix then
            prefix, keyword = split_keyword(element.text, chapter_words)
            kind = 'chapter'
          end

          if prefix and keyword then
            local number_text = inlines[index + 2].text
            if kind == 'figure' then
              local first, second, suffix = number_text:match('^(%d+)%-(%d+)(.*)$')
              if first and ok_suffix(suffix) then
                if prefix ~= '' then output:insert(pandoc.Str(prefix)) end
                output:insert(pandoc.RawInline(
                  'latex',
                  '\\crossreflink{' .. figure_label(first, second) .. '}{'
                      .. keyword .. ' ' .. first .. '-' .. second .. '}'
                ))
                if suffix ~= '' then output:insert(pandoc.Str(suffix)) end
                linked = true
              end
            else
              local number, suffix = number_text:match('^(%d+)(.*)$')
              if number and ok_suffix(suffix) then
                if prefix ~= '' then output:insert(pandoc.Str(prefix)) end
                output:insert(pandoc.RawInline(
                  'latex',
                  '\\crossreflink{' .. chapter_label(number) .. '}{'
                      .. keyword .. ' ' .. number .. '}'
                ))
                if suffix ~= '' then output:insert(pandoc.Str(suffix)) end
                linked = true
              end
            end
          end
        end

        if linked then
          index = index + 3
          changed = true
        else
          output:insert(element)
          index = index + 1
        end
      end

      if changed then return output end
    end,
  }
}
