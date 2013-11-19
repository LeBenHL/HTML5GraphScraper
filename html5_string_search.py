import threading
import time
import sys

from pygraph.algorithms.searching import depth_first_search
from html_graph_scraper import HTML5Graph

class Queue:
  def __init__(self):
      self.list = []

  def push(self,item):
      self.list.append(item)

  def pop(self):
      return self.list.pop(0)

  def isEmpty(self):
      return len(self.list) == 0

class HTML5StringSearch:

  class PrintThread(threading.Thread):

    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
        self.queue = Queue()

    def run(self):
        print "Starting " + self.name
        self.processQueue()
        print "Exiting " + self.name

    def processQueue(self):
      while True:
        time.sleep(5)
        while not self.queue.isEmpty():
          item = self.queue.pop()
          print item

  class SearchThread(threading.Thread):

    def __init__(self, name, func, print_thread):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.print_thread = print_thread
        self.searching = True

    def run(self):
        print "Starting " + self.name
        self.func()
        print "Exiting " + self.name

  def __init__(self, start_states, end_state, num_threads=1):
    self.start_states = start_states
    self.end_state = end_state
    self.graph = HTML5Graph(populate=True)
    self.html5_chars = self.allChars()
    self.string_queue = [[char] for char in self.html5_chars]
    
    self.populateAnythingElseCharDict()
    self.populateStartStateAndCharDict()

    #Threading Stuff
    print_thread = HTML5StringSearch.PrintThread("PrintThread")
    print_thread.daemon = True
    print_thread.start()
    self.num_threads = num_threads

    self.threads = []
    #Create Threads
    for i in range(self.num_threads):
      self.threads.append(HTML5StringSearch.SearchThread("Thread-%d" % i, self.findStrings, print_thread))

    for thread in self.threads:
      thread.daemon = True
      thread.start()

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
    while self.threadsStillSearching():
      while self.string_queue:
        threading.currentThread().searching = True
        html5_string = self.string_queue.pop(0)
        end_state = self.endStateFromParse(html5_string)

        if end_state and end_state == self.end_state:
          threading.currentThread().print_thread.queue.push(html5_string)
          

        for char in self.html5_chars:
          self.string_queue.append(html5_string + [char])
      threading.currentThread().searching = False

  def endStateFromParse(self, html5_string):
    try:
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
    except KeyError:
      #If Value Error, this means that we were not able to fully parse the string some state
      return None

  def parse(self, html5_string, start_state):
    current_state = start_state
    for char in html5_string:
      current_state = self.start_state_and_char_dict[current_state][char]

    return current_state

  def allChars(self):
    chars = []
    for edge in self.graph.edges():
      chars += self.graph.edge_label(edge).split(", ")

    return set(chars).difference(set(["Anything Else"]))

  def threadsStillSearching(self):
    return any([thread.searching for thread in self.threads])

if __name__ == "__main__":
  try:
    graph = HTML5Graph(populate=True)
    reachable_nodes = depth_first_search(graph, ("asciiLetters", "dataState"))[1]
    searcher = HTML5StringSearch(reachable_nodes, ("asciiLetters", "dataState"), num_threads=int(sys.argv[1]))
    while True: time.sleep(100)
  except (KeyboardInterrupt, SystemExit):
    print 'Quitting Script'

