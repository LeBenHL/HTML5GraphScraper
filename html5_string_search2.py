from collections import namedtuple
import threading
import time
import sys

from pygraph.algorithms.searching import depth_first_search
from html_graph_scraper import HTML5Graph

Node = namedtuple('Node', ['state', 'path'], verbose=False)
class Queue:
  def __init__(self):
      self.list = []

  def push(self,item):
      self.list.append(item)

  def pop(self):
      return self.list.pop(0)

  def isEmpty(self):
      return len(self.list) == 0

class Search:

  @staticmethod
  def breadthFirstSearch(problem, num_threads=1):
    return Search.MultiThreadGeneralSearch(problem, Queue(), num_threads=num_threads);
    #return Search.GeneralSearch(problem, Queue());
  
  class GeneralSearch:

    def __init__(self, problem, fringe):
      self.problem = problem
      self.fringe = fringe   
      self.closedSet = set()
      self.fringe.push(self.problem.getStartState())

      self.beginSearch()

    def beginSearch(self):
      while not self.fringe.isEmpty():
        node = self.fringe.pop()
        if (self.problem.isGoalState(node)):
          path = list(node.path)
          path.reverse()
          print(path)
        else:
          pass
        state_tuple = node.state
        if state_tuple not in self.closedSet:
            self.closedSet.add(state_tuple)
            successors = self.problem.getSuccessors(node)
            for successor in successors:
                tuple_successor = successor.state
                if tuple_successor not in self.closedSet:
                    self.fringe.push(successor)
      return node

  class BFSThread(threading.Thread):

    def __init__(self, name, func, print_thread):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.print_thread = print_thread
        self.expanding = True

    def run(self):
        print("Starting " + self.name)
        self.func()
        print("Exiting " + self.name)

  class PrintThread(threading.Thread):

    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
        self.queue = Queue()

    def run(self):
        print("Starting " + self.name)
        self.processQueue()
        print("Exiting " + self.name)

    def processQueue(self):
      while True:
        time.sleep(5)
        while not self.queue.isEmpty():
          item = self.queue.pop()
          print(item)

  class MultiThreadGeneralSearch:

    def __init__(self, problem, fringe, num_threads=1):
      self.problem = problem
      self.fringe = fringe   
      self.closedSet = set()
      self.fringe.push(self.problem.getStartState())

      #Threading Stuff
      print_thread = Search.PrintThread("PrintThread")
      print_thread.daemon = True
      print_thread.start()
      self.num_threads = num_threads

      self.threads = []
      #Create Threads
      for i in range(self.num_threads):
        self.threads.append(Search.BFSThread("Thread-%d" % i, self.beginSearch, print_thread))

      for thread in self.threads:
        thread.daemon = True
        thread.start()

    def beginSearch(self):
      while self.threadsStillExpanding():
        while not self.fringe.isEmpty():
          threading.currentThread().expanding = True
          node = self.fringePop()
          if (self.problem.isGoalState(node)):
            path = list(node.path)
            path.reverse()
            threading.currentThread().print_thread.queue.push(path)
          else:
            pass
          state_tuple = node.state
          if state_tuple not in self.closedSet:
              self.closedStateAdd(state_tuple)
              successors = self.problem.getSuccessors(node)
              for successor in successors:
                  tuple_successor = successor.state
                  if tuple_successor not in self.closedSet:
                      self.fringePush(successor)
        threading.currentThread().expanding = False

    def fringePop(self):
      return self.fringe.pop()

    def fringePush(self, node):
      self.fringe.push(node)

    def closedStateAdd(self, state_tuple):
      self.closedSet.add(state_tuple)

    def threadsStillExpanding(self):
      return any([thread.expanding for thread in self.threads])


class IllegalCharacterException(Exception):
  pass

class CommonStringSearchDict(dict):

  def __init__(self, *args):
    dict.__init__(self, args)

  def __getitem__(self, key):
    try:
      return dict.__getitem__(self, key)
    except KeyError:
      raise IllegalCharacterException()

class CommonStringSearchProblem:

  def __init__(self, graph, start_nodes, end_state):
    self.graph = graph
    self.reverse_graph = graph.reverse()
    self.start_nodes = set(start_nodes)
    self.end_state = end_state
    self.html_charset = self.allActions()
    print(self.html_charset)

    self.anything_else_characters = dict()
    for node in graph.nodes():
      actions = set()
      for neighbor in self.graph.neighbors(node):
        actions = actions.union(self.graph.edge_label((node, neighbor)).split(", "))
      self.anything_else_characters[node] = self.html_charset.difference(actions)

  def getStartState(self):
    return Node(frozenset([self.end_state]), [])

  def isGoalState(self, node):
    return self.start_nodes.issubset(node.state)

  def getSuccessors(self, node):
    successors = []
    for action in self._findAllActions(node.state):
      successors.append(self._takeAction(node, action))
    return successors

  def _takeAction(self, node, action):
    new_state = []
    for html_state in node.state:
      for neighbor in self.reverse_graph.neighbors(html_state):
        edge_label = self.reverse_graph.edge_label((html_state, neighbor))
        actions = set(edge_label.split(", "))
        if "Anything Else" in actions:
          actions.remove("Anything Else")
          actions = actions.union(self.anything_else_characters[neighbor])

        if self._contains(action, actions):
          new_state.append(neighbor)

    return Node(frozenset(new_state), node.path + [action])

  def _contains(self, action, actions):
    return action in actions

  def _findAllActions(self, state):
    actions = set()
    for html_state in state:
      for neighbor in self.reverse_graph.neighbors(html_state):
        edge_label = self.reverse_graph.edge_label((html_state, neighbor))
        action_list = set(edge_label.split(", "))
        if "Anything Else" in action_list:
          action_list.remove("Anything Else")
          action_list = action_list.union(self.anything_else_characters[neighbor])
        actions = actions.union(action_list)

    return actions

  def allActions(self):
    actions = []
    for edge in self.graph.edges():
      if '\'"\'' in self.graph.edge_label(edge):
        print(edge)
        print(self.graph.edge_label(edge))
      actions += self.graph.edge_label(edge).split(", ")

    return set(actions)

if __name__ == "__main__":
  try:
    graph = HTML5Graph(populate=True)
    reachable_nodes = depth_first_search(graph, ("asciiLetters", "dataState"))[1]
    #reachable_nodes = [("textarea", "rcdataState"), ("title", "rcdataState")]
    end_state = ("asciiLetters", "dataState")
    problem = CommonStringSearchProblem(graph, reachable_nodes, end_state)
    Search.breadthFirstSearch(problem, int(sys.argv[1]))
    while True: time.sleep(100)
  except (KeyboardInterrupt, SystemExit):
    print 'Quitting Script'

