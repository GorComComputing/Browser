import socket
import ssl
import tkinter
import tkinter.font


WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100


# Класс браузера
class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()
        self.scroll = 0		# для прокрутки экрана
        self.window.bind("<Down>", self.scrolldown)
        self.bi_times = tkinter.font.Font(
            family="Times",
            size=16,
            weight="bold",
            slant="italic",
        )


    def draw(self):
    	self.canvas.delete("all")
    	for x, y, c in self.display_list:
    		if y > self.scroll + HEIGHT: continue
    		if y + VSTEP < self.scroll: continue
    		self.canvas.create_text(x, y - self.scroll, text=c, font=self.bi_times, anchor='nw')
        
       
    # Загрузить страницу
    def load(self, url):
        headers, body = request(url)
        text = lex(body)
        
        #self.canvas.create_rectangle(10, 20, 400, 300)
        #self.canvas.create_oval(100, 100, 150, 150)
        #self.canvas.create_text(200, 150, text="Hi!")
        
        self.display_list = layout(text)
        self.draw()
        
        
    # Прокрутка вниз
    def scrolldown(self, e):
    	self.scroll += SCROLL_STEP
    	self.draw()
        

# Класс токен Текст
class Text:
    def __init__(self, text):
        self.text = text


# Класс токен Тег
class Tag:
    def __init__(self, tag):
        self.tag = tag



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
		
	port = 80 if scheme == "http" else 443
	
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
    
    
# Отобразить страницу
def lex(body):
	out = []
	text = ""
	in_tag = False
	for c in body:
		if c == "<":
			in_tag = True
			if text: out.append(Text(text))
			text = ""
		elif c == ">":
			in_tag = False
			out.append(Tag(text))
			text = ""
		else:
		#elif not in_angle:
			print(c, end="")
			text += c	
	if not in_tag and text:
		out.append(Text(text))
	return out
		
	
# Добавляет символ в список
def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    #for c in text:
    for tok in tokens:
        if isinstance(tok, Text):
            for word in tok.text.split():
    			#self.canvas.create_text(cursor_x, cursor_y, text=c)
        		display_list.append((cursor_x, cursor_y, c))
        		cursor_x += HSTEP
        		if cursor_x >= WIDTH - HSTEP:
            		cursor_y += VSTEP
            		cursor_x = HSTEP
    return display_list







