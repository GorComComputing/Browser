import parserHTML

     
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
                self.i += 1
            else:
                break
            if not (self.i > start):
                raise Exception("Parsing error word")
        return self.s[start:self.i] 
        
        
    def literal(self, literal):
        if not (self.i < len(self.s) and self.s[self.i] == literal):
            raise Exception("Parsing error pairs")
        self.i += 1
    
    
    def pair(self):
        self.whitespace()
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.word()
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
        return isinstance(node, parserHTML.Element) and self.tag == node.tag
        
        
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
    



