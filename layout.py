import tkinter.font

import browser
import parserHTML
import draw


HSTEP, VSTEP = 13, 18
FONTS = {}


# Класс макета
class BlockLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        
        
    def layout(self):
        self.display_list = []
    
        # Определяет ширину и координаты X, Y
        self.width = self.parent.width
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
        self.x = self.parent.x
        
        # Определяет по тегу блочный или линейный 
        mode = layout_mode(self.node)
        if mode == "block":
            previous = None
            for child in self.node.children:
                next = BlockLayout(child, self, previous)
                self.children.append(next)
                previous = next
        else:	 # "inline"
            self.new_line()
            self.recurse(self.node)
            
        for child in self.children:
            child.layout()
            
        self.height = sum([child.height for child in self.children])
        print("HEIGHT: ", self.node, self.height)
            
            
    def paint(self, display_list):         
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = draw.DrawRect(self.x, self.y, x2, y2, bgcolor)
            display_list.append(rect)
            
        is_atomic = not isinstance(self.node, parserHTML.Text) and \
            (self.node.tag == "input" or self.node.tag == "button")

        if not is_atomic:
            if bgcolor != "transparent":
                x2, y2 = self.x + self.width, self.y + self.height
                rect = draw.DrawRect(self.x, self.y, x2, y2, bgcolor)
                display_list.append(rect)
                
        for child in self.children:
            child.paint(display_list)
        

    def word(self, node, word):
        color = node.style["color"]
        font = self.get_font(node)
        w = font.measure(word)
        #print(word, self.cursor_x, w, font.measure(" "), self.cursor_x + w + font.measure(" "))
        if self.cursor_x + w > self.width:
            self.new_line()
        self.cursor_x += w + font.measure(" ")
        
        line = self.children[-1]
        text = TextLayout(node, word, line, self.previous_word)
        line.children.append(text)
        self.previous_word = text


    def new_line(self):
        self.previous_word = None
        self.cursor_x = 0
        last_line = self.children[-1] if self.children else None
        new_line = LineLayout(self.node, self, last_line)
        self.children.append(new_line)


    #def flush(self):
    #    if not self.line: return
    #    metrics = [font.metrics() for x, word, font, color in self.line]
    #    max_ascent = max([metric["ascent"] for metric in metrics])
    #    baseline = self.cursor_y + 1.25 * max_ascent
    #    for rel_x, word, font, color in self.line:
    #        x = self.x + rel_x
    #        y = self.y + baseline - font.metrics("ascent")
    #        self.display_list.append((x, y, word, font, color))
            
            #y = baseline - font.metrics("ascent")
            #self.display_list.append((x, y, word, font))
        #self.cursor_x = HSTEP
    #    self.cursor_x = 0
    #    self.line = []
    #    max_descent = max([metric["descent"] for metric in metrics])
    #    self.cursor_y = baseline + 1.25 * max_descent


    def recurse(self, node):
        if isinstance(node, parserHTML.Text):
            for word in node.text.split():
                self.word(node, word)
        else:
            if node.tag == "br":
                self.new_line()
            elif node.tag == "input" or node.tag == "button":
                self.input(node)
            else:
                for child in node.children:
                    self.recurse(child)
                
                
    def input(self, node):
        w = INPUT_WIDTH_PX
        if self.cursor_x + w > self.width:
            self.new_line()
        line = self.children[-1]
        input = InputLayout(node, line, self.previous_word)
        line.children.append(input)
        self.previous_word = input
        font = self.get_font(node)
        self.cursor_x += w + font.measure(" ")
            
          
    def layout_intermediate(self):
        previous = None
        for child in self.node.children:
            next = BlockLayout(child, self, previous)
            self.children.append(next)
            previous = next
            
            
    def get_font(self, node):
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(node.style["font-size"][:-2]) * .75)
        return get_font(size, weight, style)


# Класс корня документа 
class DocumentLayout:
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.children = []


    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        
        self.width = browser.WIDTH - 2*HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.height = child.height + 2*VSTEP
        
        
    def paint(self, display_list):
        self.children[0].paint(display_list)
        

# Класс строки макета   
class LineLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        
        
    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
        
        for word in self.children:
            word.layout()
    
        max_ascent = max([word.font.metrics("ascent")
                  for word in self.children])
        baseline = self.y + 1.25 * max_ascent
        for word in self.children:
            word.y = baseline - word.font.metrics("ascent")
        max_descent = max([word.font.metrics("descent")
                   for word in self.children])
                   
        self.height = 1.25 * (max_ascent + max_descent)


    def paint(self, display_list):
        for child in self.children:
            child.paint(display_list)

        
# Класс слова макета        
class TextLayout:
    def __init__(self, node, word, parent, previous):
        self.node = node
        self.word = word
        self.children = []
        self.parent = parent
        self.previous = previous
        
        
    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(self.node.style["font-size"][:-2]) * .75)
        self.font = get_font(size, weight, style)
        
        # Do not set self.y!!!
        self.width = self.font.measure(self.word)

        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")
        
        
    def paint(self, display_list):
        color = self.node.style["color"]
        display_list.append(draw.DrawText(self.x, self.y, self.word, self.font, color))
       
        
INPUT_WIDTH_PX = 200

# Класс области ввода        
class InputLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.children = []
        self.parent = parent
        self.previous = previous
        
        
    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(self.node.style["font-size"][:-2]) * .75)
        self.font = get_font(size, weight, style)
        
        # Do not set self.y!!!
        self.width = INPUT_WIDTH_PX

        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")
        
        
    def paint(self, display_list):
        # Рисует фон
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = draw.DrawRect(self.x, self.y, x2, y2, bgcolor)
            display_list.append(rect)
        # Получает текстовое содержимое элемента
        if self.node.tag == "input":
            text = self.node.attributes.get("value", "")
        elif self.node.tag == "button":
            if len(self.node.children) == 1 and \
               isinstance(self.node.children[0], parserHTML.Text):
                text = self.node.children[0].text
            else:
                print("Ignoring HTML contents inside button")
                text = ""
        # Рисует текстовое содержимое элемента        
        color = self.node.style["color"]
        display_list.append(draw.DrawText(self.x, self.y, text, self.font, color))

        


BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
]        
   
# Определяет по тегу блочный или линейный        
def layout_mode(node):
    if isinstance(node, parserHTML.Text):
        return "inline"
    elif node.children:
        for child in node.children:
            if isinstance(child, parserHTML.Text): continue
            if child.tag in BLOCK_ELEMENTS:
                return "block"
        return "inline"
    elif node.tag == "input":
        return "inline"
    else:
        return "block"
     
        
def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]                
        

       
        
      
