import socket
import ssl
import tkinter


import draw
import parserCSS
import parserHTML
import layout


INHERITED_PROPERTIES = {
    "font-size": "16px",
    "font-style": "normal",
    "font-weight": "normal",
    "color": "black",
}
WIDTH, HEIGHT = 800, 600
SCROLL_STEP = 100
CHROME_PX = 100


# Класс браузера
class Browser:
    def __init__(self):
        # Создать окно
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT,
            bg="white",
        )
        self.canvas.pack()
        
        self.tabs = []
        self.active_tab = None
        
        self.focus = None
        self.address_bar = ""
        
        # Обработчики событий
        self.window.bind("<Down>", self.handle_down)
        self.window.bind("<Up>", self.handle_up)
        self.window.bind("<Button-1>", self.handle_click)
        self.window.bind("<Key>", self.handle_key)
        self.window.bind("<Return>", self.handle_enter)


    def load(self, url):
        new_tab = Tab()
        new_tab.load(url)
        self.active_tab = len(self.tabs)
        self.tabs.append(new_tab)
        self.draw()


    def draw(self):
        # Очистить канву
        self.canvas.delete("all")
        self.tabs[self.active_tab].draw(self.canvas)
        
        # Вывести на канву хром браузера
        for cmd in self.paint_chrome():
            cmd.execute(0, self.canvas)
        
        
    def paint_chrome(self):
        cmds = []
        cmds.append(draw.DrawRect(0, 0, WIDTH, CHROME_PX, "white"))
        cmds.append(draw.DrawLine(0, CHROME_PX - 1, WIDTH, CHROME_PX - 1, "black", 1))
        tabfont = layout.get_font(16, "normal", "roman")
        for i, tab in enumerate(self.tabs):
            name = "Tab {}".format(i)
            x1, x2 = 40 + 80 * i, 120 + 80 * i
            cmds.append(draw.DrawLine(x1, 0, x1, 40, "black", 1))
            cmds.append(draw.DrawLine(x2, 0, x2, 40, "black", 1))
            cmds.append(draw.DrawText(x1 + 10, 10, name, tabfont, "black"))
            if i == self.active_tab:
                cmds.append(draw.DrawLine(0, 40, x1, 40, "black", 1))
                cmds.append(draw.DrawLine(x2, 40, WIDTH, 40, "black", 1))
        # Рисуем кнопку "Добавить вкладку"
        buttonfont = layout.get_font(20, "normal", "roman")
        cmds.append(draw.DrawOutline(10, 10, 30, 30, "black", 1))
        cmds.append(draw.DrawText(10, 4, "+", buttonfont, "black"))
        # Рисуем адресную строку
        cmds.append(draw.DrawOutline(40, 50, WIDTH - 10, 90, "black", 1))
        if self.focus == "address bar":
            cmds.append(draw.DrawText(55, 55, self.address_bar, buttonfont, "black"))
            w = buttonfont.measure(self.address_bar)
            cmds.append(draw.DrawLine(55 + w, 55, 55 + w, 85, "black", 1))
        else:
            url = self.tabs[self.active_tab].url
            cmds.append(draw.DrawText(55, 55, url, buttonfont, "black"))
        # Рисуем кнопку "Назад"
        cmds.append(draw.DrawOutline(10, 50, 35, 90, "black", 1))
        cmds.append(draw.DrawText(11, 55, "<", buttonfont, "black"))
        return cmds
    
        
    def handle_down(self, e):
        self.tabs[self.active_tab].scrolldown()
        self.draw()
        
        
    def handle_up(self, e):
        self.tabs[self.active_tab].scrollup()
        self.draw()


    def handle_click(self, e):
        if e.y < CHROME_PX:
            if 40 <= e.x < 40 + 80 * len(self.tabs) and 0 <= e.y < 40:
                self.active_tab = int((e.x - 40) / 80)
            elif 10 <= e.x < 30 and 10 <= e.y < 30:
                self.load("https://browser.engineering/")
            elif 10 <= e.x < 35 and 50 <= e.y < 90:
                self.tabs[self.active_tab].go_back()
            elif 50 <= e.x < WIDTH - 10 and 50 <= e.y < 90:
                self.focus = "address bar"
                self.address_bar = ""
        else:
            self.tabs[self.active_tab].click(e.x, e.y - CHROME_PX)
        self.draw()
        
        
    # Обработчик нажатия клавиш      
    def handle_key(self, e):
        if len(e.char) == 0: return
        if not (0x20 <= ord(e.char) < 0x7f): return

        if self.focus == "address bar":
            self.address_bar += e.char
            self.draw()
            
            
    # Обработчик нажатия Enter       
    def handle_enter(self, e):
        if self.focus == "address bar":
            self.tabs[self.active_tab].load(self.address_bar)
            self.focus = None
            self.draw()
            
            
    
 
 
# Класс вкладки
class Tab:
    def __init__(self):
        self.scroll = 0		# для прокрутки экрана
        self.url = None
        self.history = []
        with open("browser.css") as f:
            self.default_style_sheet = parserCSS.CSSParser(f.read()).parse()  
            
            
    def load(self, url):
        self.url = url
        self.history.append(url)
        # Загрузить страницу
        #headers, body = request("http://info.cern.ch/hypertext/WWW/TheProject.html")
        headers, body = request(url)
        #body = requestFile('index.html')
        
        # Парсинг HTML
        self.nodes = parserHTML.HTMLParser(body).parse()
        #parserHTML.print_tree(self.nodes)
        
        # Загрузка CSS
        rules = self.default_style_sheet.copy()
        links = [node.attributes["href"]
             for node in tree_to_list(self.nodes, [])
             if isinstance(node, parserHTML.Element)
             and node.tag == "link"
             and "href" in node.attributes
             and node.attributes.get("rel") == "stylesheet"]
        for link in links:
            try:
                #header, body = request(resolve_url(link, url))
                body = requestFile(link)
            except:
                continue
            rules.extend(parserCSS.CSSParser(body).parse())
        self.style(self.nodes, sorted(rules, key=cascade_priority))
    
        # Построение макета страницы
        self.document = layout.DocumentLayout(self.nodes)
        self.document.layout()
        
        # Рендеринг макета
        self.display_list = []
        self.document.paint(self.display_list)
        #self.draw() 
            
            
    def draw(self, canvas):
        # Вывести на канву все элементы дерева
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT - CHROME_PX: continue
            if cmd.bottom < self.scroll: continue
            cmd.execute(self.scroll - CHROME_PX, canvas)    
           
            
    def style(self, node, rules):
        node.style = {}
        
        # Заполнить стили браузера по умолчанию
        for property, default_value in INHERITED_PROPERTIES.items():
            if node.parent:
                node.style[property] = node.parent.style[property]
            else:
                node.style[property] = default_value
        
        # Заполнить стили загруженные из файлов *.css
        for selector, body in rules:
            if not selector.matches(node): continue
            for property, value in body.items():
                node.style[property] = value
    
        # Заполнить стили из атрибутов тегов
        if isinstance(node, parserHTML.Element) and "style" in node.attributes:
            pairs = parserCSS.CSSParser(node.attributes["style"]).body()
            for property, value in pairs.items():
                node.style[property] = value
            
        #print(node.style) 
        
        # Размеры шрифта от % к px 
        if node.style["font-size"].endswith("%"):
            if node.parent:
                parent_font_size = node.parent.style["font-size"]
            else:
                parent_font_size = INHERITED_PROPERTIES["font-size"]
            node_pct = float(node.style["font-size"][:-1]) / 100
            parent_px = float(parent_font_size[:-2])
            node.style["font-size"] = str(node_pct * parent_px) + "px"
            
        # Рекурсивно пройти все дерево
        for child in node.children:
            self.style(child, rules)
            
            
    # Возвращение назад       
    def go_back(self):
        if len(self.history) > 1:
            self.history.pop()
            back = self.history.pop()
            self.load(back)
        
        
	# Прокрутка вниз (обработчик клавиши "Стрелка вниз")   
    def scrolldown(self):
    	max_y = self.document.height - (HEIGHT - CHROME_PX)
    	self.scroll = min(self.scroll + SCROLL_STEP, max_y)
    	#self.draw()
    	
    	
    # Прокрутка вверх (обработчик клавиши "Стрелка вверх")   
    def scrollup(self):
    	min_y = 0 
    	self.scroll = max(self.scroll - SCROLL_STEP, min_y)
    	#self.draw()
    	
    	
    # Обработчик клика левой кнопкой мыши	
    def click(self, x, y):
        #x, y = e.x, e.y
        y += self.scroll
        print(x, y)
        # Поиск в дереве объектов на которых кликнули
        objs = [obj for obj in tree_to_list(self.document, [])
        	if obj.x <= x < obj.x + obj.width
        	and obj.y <= y < obj.y + obj.height]
        # Выбор последнего
        if not objs: return
        elt = objs[-1].node
        print(elt)
        while elt:
            if isinstance(elt, parserHTML.Text):
                pass
            elif elt.tag == "a" and "href" in elt.attributes:
                link = elt.attributes["href"].strip('\"')
                url = resolve_url(link, self.url)
                return self.load(url)
            elt = elt.parent
        
        

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
    scheme, host, port, path = parse_url(url)

    scheme, url = url.split("://", 1)
    assert scheme in ["http", "https"], "Unknown scheme {}".format(scheme)
    
    s = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )

    if scheme == "http" and port == "":
        port = 80  
    if scheme == "https" and port == "":
        port = 443 

    if scheme == "https":
        ctx = ssl.create_default_context()
        s = ctx.wrap_socket(s, server_hostname=host)

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
    #assert status == "200", "{}: {}".format(status, explanation)

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
	return body
	

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
    

def tree_to_list(tree, list):
    list.append(tree)
    for child in tree.children:
        tree_to_list(child, list)
    return list    
    		
	


