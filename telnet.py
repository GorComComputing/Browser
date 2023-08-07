import socket
import ssl

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

    # Соединение
	s.connect((host, 80))

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
def show(body):
	in_angle = False
	for c in body:
		if c == "<":
			in_angle = True
		elif c == ">":
			in_angle = False
		elif not in_angle:
			print(c, end="")


# Загрузить страницу
def load(url):
    headers, body = request(url)
    show(body)
