-- Use high-resolution browser renders for PDF because librsvg does not honor
-- SVG textLength consistently and can distort Russian diagram labels.

local image_dir = os.getenv("AI_AGENT_BOOK_PDF_IMAGE_DIR")

function Image(image)
  if not image.src:match("%.svg$") then
    return image
  end
  if image_dir == nil or image_dir == "" then
    error("AI_AGENT_BOOK_PDF_IMAGE_DIR is not set")
  end
  local basename = image.src:match("([^/]+)%.svg$")
  if basename == nil then
    error("Cannot resolve SVG filename: " .. image.src)
  end
  image.src = image_dir .. "/" .. basename .. ".png"
  return image
end
