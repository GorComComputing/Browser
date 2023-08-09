import socket
import ssl
import tkinter
import tkinter.font


WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

FONTS = {}

INHERITED_PROPERTIES = {
    "font-size": "16px",
    "font-style": "normal",
    "font-weight": "normal",
    "color": "black",
}


# Класс браузера
class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT,
            bg="white",
        )
        self.canvas.pack()
        self.scroll = 0		# для прокрутки экрана
        self.window.bind("<Down>", self.scrolldown)
        
        with open("browser.css") as f:
            self.default_style_sheet = CSSParser(f.read()).parse()


    def draw(self):
        self.canvas.delete("all")
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT: continue
            if cmd.bottom < self.scroll: continue
            cmd.execute(self.scroll, self.canvas)
            
    	#self.canvas.delete("all")
    	#for x, y, c, font in self.display_list:
    	#	if y > self.scroll + HEIGHT: continue
    	#	if y + VSTEP < self.scroll: continue
    	#	self.canvas.create_text(x, y - self.scroll, text=c, font=font, anchor=tkinter.NE)
        
       
    # Загрузить страницу
    def load(self, url):
        #headers, body = request("http://info.cern.ch/hypertext/WWW/TheProject.html")
        #headers, body = request(url)
        body = requestFile('index.html')
        
        self.nodes = HTMLParser(body).parse()
        #self.display_list = Layout(self.nodes).display_list
        
        rules = self.default_style_sheet.copy()
        
        links = [node.attributes["href"]
             for node in tree_to_list(self.nodes, [])
             if isinstance(node, Element)
             and node.tag == "link"
             and "href" in node.attributes
             and node.attributes.get("rel") == "stylesheet"]
        print(links)
        
        for link in links:
            try:
                #header, body = request(resolve_url(link, url))
                body = requestFile(link)
            except:
                continue
            rules.extend(CSSParser(body).parse())
             
        self.style(self.nodes, sorted(rules, key=cascade_priority))
        #self.style(self.nodes, rules)
    
        #self.style(self.nodes)
        self.document = DocumentLayout(self.nodes)
        
        self.document.layout()
        #self.display_list = self.document.display_list

        #nodes = HTMLParser(body).parse()
        print_tree(self.nodes)

        #tokens = lex(body)     
        #self.display_list = Layout(tokens).display_list
        #print(self.display_list)
        self.display_list = []
        self.document.paint(self.display_list)
        self.draw()
        #import dukpy
        #print(dukpy.evaljs("2 + 2"))
        
        
    def style(self, node, rules):
        node.style = {}
        
        for property, default_value in INHERITED_PROPERTIES.items():
            if node.parent:
                node.style[property] = node.parent.style[property]
            else:
                node.style[property] = default_value
        
        for selector, body in rules:
            if not selector.matches(node): continue
            for property, value in body.items():
                node.style[property] = value
    
        if isinstance(node, Element) and "style" in node.attributes:
            #print(node.attributes["style"])
            pairs = CSSParser(node.attributes["style"]).body()
            #print(pairs)
            for property, value in pairs.items():
                node.style[property] = value
            
        print(node.style) 
        
        if node.style["font-size"].endswith("%"):
            if node.parent:
                parent_font_size = node.parent.style["font-size"]
            else:
                parent_font_size = INHERITED_PROPERTIES["font-size"]
            node_pct = float(node.style["font-size"][:-1]) / 100
            parent_px = float(parent_font_size[:-2])
            node.style["font-size"] = str(node_pct * parent_px) + "px"
            
        for child in node.children:
            self.style(child, rules)
            
        
            
        
    # Прокрутка вниз
    def scrolldown(self, e):
    	max_y = self.document.height - HEIGHT
    	self.scroll = min(self.scroll + SCROLL_STEP, max_y)
    	#self.scroll += SCROLL_STEP
    	self.draw()
    	

# Класс токен Текст
class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = []
        self.parent = parent
        self.style = {}


    def __repr__(self):
        return repr(self.text)


# Класс токен Тег
class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent
        self.style = {}
        
        
    def __repr__(self):
        return "<" + self.tag + ">"


# Класс макета
class BlockLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        
        
    def layout(self):
        print(self.node.style)
        self.width = self.parent.width
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
        self.x = self.parent.x
        mode = layout_mode(self.node)
        print(mode)
        self.display_list = []
        if mode == "block":
            previous = None
            for child in self.node.children:
                next = BlockLayout(child, self, previous)
                self.children.append(next)
                previous = next
        else:
            self.cursor_x = 0
            self.cursor_y = 0
            self.weight = "normal"
            self.style = "roman"
            self.size = 16

            self.line = []
            self.recurse(self.node)
            self.flush()
            
        for child in self.children:
            child.layout()
        #for child in self.children:
        #    self.display_list.extend(child.display_list)
            
        if mode == "block":
            self.height = sum([child.height for child in self.children])
        else:
            self.height = self.cursor_y
            
            
    def paint(self, display_list):
        if isinstance(self.node, Element) and self.node.tag == "pre":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, "gray")
            display_list.append(rect)
            
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
            display_list.append(rect)
            
        for x, y, word, font, color in self.display_list:
            display_list.append(DrawText(x, y, word, font, color))
            
        #display_list.extend(self.display_list)
        for child in self.children:
            child.paint(display_list)
        

    def word(self, node, word):
        color = node.style["color"]
        font = self.get_font(node)
        w = font.measure(word)
        print(word, self.cursor_x, w, font.measure(" "), self.cursor_x + w + font.measure(" "))
        if self.cursor_x + w > self.width:
            self.flush()
            #self.cursor_y += font.metrics("linespace") * 1.25
            #self.cursor_x = HSTEP
        self.cursor_x += w + font.measure(" ")
        #self.display_list.append((self.cursor_x, self.cursor_y, word, font))
        self.line.append((self.cursor_x, word, font, color))


    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font, color in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        for rel_x, word, font, color in self.line:
            x = self.x + rel_x
            y = self.y + baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font, color))
            
            #y = baseline - font.metrics("ascent")
            #self.display_list.append((x, y, word, font))
        #self.cursor_x = HSTEP
        self.cursor_x = 0
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent


    #def open_tag(self, tag):
    #    if tag == "i":
    #        self.style = "italic"
    #    elif tag == "b":
    #        self.weight = "bold"
    #    elif tag == "small":
    #        self.size -= 2
    #    elif tag == "big":
    #        self.size += 4



    #def close_tag(self, tag):
    #    if tag == "i":
    #        self.style = "roman"
    #    elif tag == "b":
    #        self.weight = "normal"
    #    elif tag == "small":
    #        self.size += 2
    #    elif tag == "big":
    #        self.size -= 4
    #    elif tag == "p":
    #        self.flush()
    #        self.cursor_y += VSTEP
    #    elif tag == "h1":
    #        self.flush()
    #        self.cursor_y += VSTEP
    #    elif tag == "br":
    #        self.flush()


    def recurse(self, node):
        if isinstance(node, Text):
            for word in node.text.split():
                self.word(node, word)
        else:
            if node.tag == "br":
                self.flush()
            for child in node.children:
                self.recurse(child)
            
            #self.open_tag(node.tag)
            #for child in node.children:
            #    self.recurse(child)
            #self.close_tag(node.tag)
            
          
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
        
        self.width = WIDTH - 2*HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.height = child.height + 2*VSTEP
        
        #self.display_list = child.display_list
        
        
    def paint(self, display_list):
        self.children[0].paint(display_list)
        

# Класс парсера HTML
class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished = []
        
    SELF_CLOSING_TAGS = [
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    ]

    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script",
    ]
        
        
    # Отобразить страницу
    def parse(self):
        text = ""
        in_tag = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if text: self.add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c	
        if not in_tag and text:
            self.add_text(text)
        return self.finish()


    def add_text(self, text):
        if text.isspace(): return
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)
        
        
    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"): return
        self.implicit_tags(tag)
        if tag.startswith("/"):
            if len(self.unfinished) == 1: return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS:
        	parent = self.unfinished[-1]
        	node = Element(tag, attributes, parent)
        	parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)
        
    
    def finish(self):
        if len(self.unfinished) == 0:
            self.add_tag("html")
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()
        
        
    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].lower()
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                attributes[key.lower()] = value
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]
            else:
                attributes[attrpair.lower()] = ""
        return tag, attributes
        
        
    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")
            else:
                break
      
      
# Класс парсера CSS    
class CSSParser:
    def __init__(self, s):
        self.s = s
        self.i = 0       
            
           
    def whitespace(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1
        
        
    def word(self):
        start = self.i
        while self.i < len(self.s):
            if self.s[self.i].isalnum() or self.s[self.i] in "#-.%":
                #print("+", self.i, len(self.s))
                self.i += 1
            else:
                #print("-", self.i, len(self.s))
                break
            if not (self.i > start):
                raise Exception("Parsing error word")
        #print(self.s[start:self.i])
        return self.s[start:self.i]
            

    #def literal(self, literal):
        #if not (self.i < len(self.s) and self.s[self.i] == literal):
            #raise Exception("Parsing error literal")
        #self.i += 1
        
        
    def literal(self, literal):
        if not (self.i < len(self.s) and self.s[self.i] == literal):
            raise Exception("Parsing error pairs")
        self.i += 1
    
    
    def pair(self):
        self.whitespace()
        #print("_", self.i, len(self.s))
        prop = self.word()
        #print("prop", prop)
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.word()
        #print(prop.lower(), val)
        return prop.lower(), val
        
        
    def body(self):
        pairs = {}
        while self.i < len(self.s) and self.s[self.i] != "}":
            #try:
                prop, val = self.pair()
                pairs[prop.lower()] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            #except Exception:
            #	 why = self.ignore_until([";", "}"])
            #    if why == ";":
            #        self.literal(";")
            #        self.whitespace()
            #    else:
            #        break
        return pairs
    
    
    def ignore_until(self, chars):
        while self.i < len(self.s):
            if self.s[self.i] in chars:
                return self.s[self.i]
            else:
                self.i += 1
                
                
    def selector(self):
        out = TagSelector(self.word().lower())
        self.whitespace()
        while self.i < len(self.s) and self.s[self.i] != "{":
            tag = self.word()
            descendant = TagSelector(tag.lower())
            out = DescendantSelector(out, descendant)
            self.whitespace()
        return out
    
    
    def parse(self):
        rules = []
        while self.i < len(self.s):
            try:
                self.whitespace()
                selector = self.selector()
                self.literal("{")
                self.whitespace()
                body = self.body()
                self.literal("}")
                rules.append((selector, body))
            except Exception:
                why = self.ignore_until(["}"])
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break
        return rules
                
 
# Класс селектора тегов для CSS               
class TagSelector:
    def __init__(self, tag):
        self.tag = tag
        self.priority = 1
        
        
    def matches(self, node):
        return isinstance(node, Element) and self.tag == node.tag
        
        
# Класс селектора потомков для CSS      
class DescendantSelector:
    def __init__(self, ancestor, descendant):
        self.ancestor = ancestor
        self.descendant = descendant
        self.priority = ancestor.priority + descendant.priority
        
        
    def matches(self, node):
        if not self.descendant.matches(node): return False
        while node.parent:
            if self.ancestor.matches(node.parent): return True
            node = node.parent
        return False
    
                
# Класс рисует текст    
class DrawText:
    def __init__(self, x1, y1, text, font, color):
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font
        self.bottom = y1 + font.metrics("linespace")
        self.color = color
        
        
    def execute(self, scroll, canvas):
        canvas.create_text(
            self.left, self.top - scroll,
            text=self.text,
            font=self.font,
            anchor=tkinter.NE,
            fill=self.color,
        )
        

# Класс рисует фон    
class DrawRect:
    def __init__(self, x1, y1, x2, y2, color):
        self.top = y1
        self.left = x1
        self.bottom = y2
        self.right = x2
        self.color = color
        
        
    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.left, self.top - scroll,
            self.right, self.bottom - scroll,
            width=0,
            fill=self.color,
        )
        
        
# Парсинг URL
def parse_url(url):
	scheme, url = url.split("://", 1)
	if "/" not in url: 
		url = url + "/" 
	host, path = url.split("/", 1) 
	if ":" in host:
		host, port = host.split(":", 1)
		port = int(port)
	else:
		port = ""
	return (scheme, host, port, "/" + path)
	

# Запрос на сервер по URL
def request(url):
	#assert url.startswith("http://")
	#url = url[len("http://"):]
	print (url)
	scheme, host, port, path = parse_url(url)
	print (scheme, host, port, path)

	scheme, url = url.split("://", 1)
	assert scheme in ["http", "https"], "Unknown scheme {}".format(scheme)
    	
	s = socket.socket(
    	family=socket.AF_INET,
		type=socket.SOCK_STREAM,
		proto=socket.IPPROTO_TCP,
	)
		
	if scheme == "http" and port == "":
		port = 80  #else 443
	if scheme == "https" and port == "":
		port = 443 
	
	if scheme == "https":
		ctx = ssl.create_default_context()
		s = ctx.wrap_socket(s, server_hostname=host)
	
	print(host, port)

    # Соединение
	s.connect((host, port))

	# Запрос на сервер
	print(s.send("GET {} HTTP/1.0\r\n".format(path).encode("utf8") + 
       "Host: {}\r\n\r\n".format(host).encode("utf8")))

	# Ответ от сервера
	response = s.makefile("r", encoding="utf8", newline="\r\n")

	# Парсим ответ
	statusline = response.readline()
	version, status, explanation = statusline.split(" ", 2)
	assert status == "200", "{}: {}".format(status, explanation)
	
	headers = {}
	while True:
		line = response.readline()
		if line == "\r\n": break
		header, value = line.split(":", 1)
		headers[header.lower()] = value.strip()
    
	assert "transfer-encoding" not in headers
	assert "content-encoding" not in headers

	body = response.read()
	s.close()
	return headers, body
    
    
# Чтение из файла
def requestFile(name):
	f = open(name)
	body = f.read()
	print(body)
	return body
    		

def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]


def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)
        
        
BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
]
        
        
def layout_mode(node):
    if isinstance(node, Text):
        return "inline"
    elif node.children:
        if any([isinstance(child, Element) and \
                child.tag in BLOCK_ELEMENTS
                for child in node.children]):
            return "block"
        else:
            return "inline"
    else:
        return "block"


def tree_to_list(tree, list):
    list.append(tree)
    for child in tree.children:
        tree_to_list(child, list)
    return list


def resolve_url(url, current):
    if "://" in url:
        return url
    elif url.startswith("/"):
        scheme, hostpath = current.split("://", 1)
        host, oldpath = hostpath.split("/", 1)
        return scheme + "://" + host + url
    else:
        dir, _ = current.rsplit("/", 1)
        while url.startswith("../"):
            url = url[3:]
            if dir.count("/") == 2: continue
            dir, _ = dir.rsplit("/", 1)
        return dir + "/" + url
        
        
def cascade_priority(rule):
    selector, body = rule
    return selector.priority

