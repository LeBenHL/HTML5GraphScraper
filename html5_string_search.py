from html_graph_scraper import HTML5Graph

class HTML5StringSearch:

  def __init__(self, start_states, end_state):
    self.start_states = start_states
    self.end_state = end_state
    self.graph = HTML5Graph()
    self.html5_chars = self.allChars()
    
    self.populateAnythingElseCharDict()
    self.populateStartStateAndCharDict()

    self.findStrings()

  def populateAnythingElseCharDict(self):
    self.anything_else_chars_dict = dict()
    for node in self.graph.nodes():
      chars = set()
      for neighbor in self.graph.neighbors(node):
        chars = chars.union(self.graph.edge_label((node, neighbor)).split(", "))
      self.anything_else_chars_dict[node] = self.html5_chars.difference(chars)

  def populateStartStateAndCharDict(self):
    self.start_state_and_char_dict = dict()
    for node in self.graph.nodes():
      char_dict = dict()
      for neighbor in self.graph.neighbors(node):
        for char in self.graph.edge_label((node, neighbor)).split(", "):
          if char == "Anything Else":
            for anything_else_char in self.anything_else_chars_dict[node]:
              char_dict[anything_else_char] = neighbor
          else:
            char_dict[char] = neighbor
      self.start_state_and_char_dict[node] = char_dict

  def findStrings(self):
    string_queue = [[char] for char in self.html5_chars]
    #start_string = ["<", "/", "textarea"]
    #string_queue = [start_string]
    while string_queue:
      html5_string = string_queue.pop(0)
      end_state = self.end_state_from_parse(html5_string)
      print html5_string

      if end_state and end_state == self.end_state:
        return

      for char in self.html5_chars:
        string_queue.append(html5_string + [char])

  def end_state_from_parse(self, html5_string):
    end_state = None
    for start_state in self.start_states:
      if end_state:
        if end_state != self.parse(html5_string, start_state):
          return None
        else:
          pass
      else:
        end_state = self.parse(html5_string, start_state)

    return end_state

  def parse(self, html5_string, start_state):
    current_state = start_state
    for char in html5_string:
      current_state = self.start_state_and_char_dict[current_state][char]

    return current_state

  def allChars(self):
    chars = []
    for edge in self.graph.edges():
      #if '\'"\'' in graph.edge_label(edge):
      #  print edge
      #  print graph.edge_label(edge)
      chars += self.graph.edge_label(edge).split(", ")

    return set(chars).difference(set(["Anything Else"]))

if __name__ == "__main__":
  searcher = HTML5StringSearch([("textarea", "rcdataState")], ("asciiLetters", "dataState"))

