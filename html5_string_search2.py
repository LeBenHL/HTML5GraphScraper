from collections import namedtuple

from html_graph_scraper import HTML5Graph
from pygraph.classes.digraph import digraph

Node = namedtuple('Node', ['state', 'path'], verbose=False)
class Queue:
  def __init__(self):
      self.list = []

  def push(self,item):
      self.list.insert(0,item)

  def pop(self):
      return self.list.pop()

  def isEmpty(self):
      return len(self.list) == 0

class Search:

  @staticmethod
  def breadthFirstSearch(problem):
    return Search._generalSearch(problem, Queue());
  
  @staticmethod
  def _generalSearch(problem, fringe):    
    closedSet = set()
    moveList = []
    cost = 0
    fringe.push(problem.getStartState())
    while not fringe.isEmpty():
      node = fringe.pop()
      if (problem.isGoalState(node)):
        path = list(node.path)
        path.reverse()
        print path
      else:
        pass
      state_tuple = tuple(node.state)
      if state_tuple not in closedSet:
          closedSet.add(state_tuple)
          successors = problem.getSuccessors(node)
          for successor in successors:
              tuple_successor = tuple(successor.state)
              if tuple_successor not in closedSet:
                  fringe.push(successor)
    return node

class IllegalCharacterException(Exception):
  pass

class IllegalActionException(Exception):
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
    print self.html_charset

    self.anything_else_characters = dict()
    for node in graph.nodes():
      actions = set()
      for neighbor in self.graph.neighbors(node):
        actions = actions.union(self.graph.edge_label((node, neighbor)).split(", "))
      self.anything_else_characters[node] = self.html_charset.difference(actions)

  def getStartState(self):
    return Node(set([self.end_state]), [])

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

    return Node(set(new_state), node.path + [action])

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
        print edge
        print self.graph.edge_label(edge)
      actions += self.graph.edge_label(edge).split(", ")

    return set(actions)

if __name__ == "__main__":
  graph = HTML5Graph(populate=True)
  reachable_nodes = [("textarea", "rcdataState")]
  end_state = ("asciiLetters", "dataState")
  problem = CommonStringSearchProblem(graph, reachable_nodes, end_state)
  Search.breadthFirstSearch(problem).path

