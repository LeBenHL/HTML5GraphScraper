import re
from collections import namedtuple

from html5lib.constants import *
from pygraph.classes.digraph import digraph, AdditionError
from pygraph.algorithms.searching import depth_first_search
from pygraph.algorithms.minmax import heuristic_search

state_node_pattern = "[\s]*def ([^\s]*State)\("
edge_label_pattern = "[\s]*(elif|if) data (in|==|is) ([^:]*):"
else_pattern = "[\s]*else:"
end_node_pattern = "[\s]*self\.state = self\.([^\s]*)"
parse_error_pattern = '.*tokenTypes\["ParseError"\].*'

#Tag Names that are special because are tags that cause the HTML5 Tree Generator to switch to parsing into rawtext states and rcdata states
special_tags = rcdataElements.union(cdataElements)

#All other tags just consist of ASCII Letters i.e div, p, ul
other_tags = set(["asciiLetters"])
all_tags_unicode = special_tags.union(other_tags)

#Change all tags from unicode to ASCII
all_tags = []
for tag in all_tags_unicode:
  if tag is not None:
    all_tags.append(tag.encode('ascii', 'ignore'))
  else:
    all_tags.append(tag)

#Class that allows us to read in the next line and undo a single readline if necessary
class UndoFile(file):
  
  def __init__ (self, fileObj):
    self.file = fileObj
    self.prevPos = None

  def readline(self):
    self.prevPos = self.file.tell()
    return self.file.readline()

  def undoReadLine(self):
    self.file.seek(self.prevPos)

class HTML5Graph(digraph):

  def __init__(self, populate=False):
    super(HTML5Graph, self).__init__()
    if populate:
      self.parseNodes()
      self.parseEdges()

  def parseNodes(self):
    f = open("tokenizer.py", "r")
    for line in f:
      match = re.match(state_node_pattern, line)
      if match:
        state_node = match.group(1)

        #Create a tuple for every possible (tag, state_node) tuple. In this representation, 
        for tag in all_tags:
          self.add_node((tag, state_node))

  def parseEdges(self):
    f = UndoFile(open("tokenizer.py", "r"))
    line = f.readline()
    while line:
      match = re.match(state_node_pattern, line)
      if match:
        outgoing_node = match.group(1)
        if outgoing_node == "markupDeclarationOpenState":
          #If we are doing markup declaration state, just add an edge to the comment state.
          #We probably don't want to go near DOCTYPE and CDATA state
          #TODO BETTER MARKUPDECLARATION STATE
          self.addEdgeForTags(("markupDeclarationOpenState", "commentState"), "--", all_tags)
          self.addEdgeForTags(("markupDeclarationOpenState", "markupDeclarationOpenState"), "Anything Else", all_tags)
        elif outgoing_node == "cdataSectionState":
          #Parsing this is quite difficult, I rather add the edges in by hand
          self.addEdgeForTags(("cdataSectionState", "dataState"), "]]>", all_tags)
          self.addEdgeForTags(("cdataSectionState", "cdataSectionState"), "Anything Else", all_tags)
        elif outgoing_node == "bogusCommentState":
          #Bogus Comment State weirdly formatted too
          self.addEdgeForTags(("bogusCommentState", "dataState"), ">", all_tags)
          self.addEdgeForTags(("bogusCommentState", "bogusCommentState"), "Anything Else", all_tags)
        else:
          #Else parse labels normally
          self._parseEdgeLabels(outgoing_node, f)

      line = f.readline()

  def _parseEdgeLabels(self, outgoing_node, f):
    line = f.readline()
    while line:
      match = re.match(state_node_pattern, line)
      if match:
        #We see a new state node! We need to parse new edges
        f.undoReadLine()
        break

      if "self.consumeEntity()" in line:
        #Weird case where we consume an entity and then return back to the corresponding data state
        if outgoing_node == "entityDataState":
          self.addEdgeForTags((outgoing_node, "dataState"), "entity;", all_tags)
          self.addEdgeForTags((outgoing_node, "entityDataState"), "Anything Else", all_tags)
        elif outgoing_node == "characterReferenceInRcdataState":
          self.addEdgeForTags((outgoing_node, "rcdataState"), "entity;", all_tags)
          self.addEdgeForTags((outgoing_node, "characterReferenceInRcdataState"), "Anything Else", all_tags)
        else:
          print "WARNING: Unexpected consume entity for " + outgoing_node

        line = f.readline()
        continue

      match = re.match(edge_label_pattern, line)
      if match:
        label = match.group(3)
        #We don't care about EOF edges. We are never going to inject a EOF token into the page anyways
        if not label == "EOF":
          label = self._sanitize(label)
          self._parseEdgeEndNodes(outgoing_node, label, f)

        line = f.readline()
        continue

      match = re.match(else_pattern, line)
      if match:
        #Default case
        label = "Anything Else"
        self._parseEdgeEndNodes(outgoing_node, label, f)

        line = f.readline()
        continue

      line = f.readline()

  def _sanitize(self, label):
    and_appropriate_pattern = '(.*) and appropriate'
    match = re.match(and_appropriate_pattern, label)

    if (label.startswith('"') and label.endswith('"')) or (label.startswith("'") and label.endswith("'")):
      #Evaluate the string if we detect it as a string to strip the quotes and escape chars 
      label = eval(label)
    elif label.startswith('(') and label.endswith(')'):
      if label == '(spaceCharacters | frozenset(("/", ">")))':
        #Hacky. I will just manually set the label when it looks like the above string
        label = "spaceCharacters, /, >"
      else:
        #If in parens, evaluate it to get the value as a tuple or frozenset and convert it to a string delimited by commas
        label = ', '.join(eval(label))
    elif match:
      #If ends with and appropriate, get rid of the and appropriate line. We don't really care too much for it
      label = match.group(1)

    return label

  def _parseEdgeEndNodes(self, outgoing_node, label, f):
    line = f.readline()
    found_end_node = False
    while line:
      match = re.match(parse_error_pattern, line)
      if match:
        #Parse Error! We want to silently ignore the fact that we get parsing errors here
        pass

      match = re.match(edge_label_pattern, line)
      if match:
          #We see a new edge label node! We need to parse new edge end nodes
          if not found_end_node:
            #If we never found an end node, this probably means that this edge was meant to be a self edge
            edge = (outgoing_node, outgoing_node)
            self.addEdgeForTags(edge, label, all_tags)

          f.undoReadLine()
          break

      match = re.match(else_pattern, line)
      if match:
          #We see a new edge label node! We need to parse new edge end nodes
          if not found_end_node:
            #If we never found an end node, this probably means that this edge was meant to be a self edgee
            edge = (outgoing_node, outgoing_node)
            self.addEdgeForTags(edge, label, all_tags)

          f.undoReadLine()
          break

      match = re.match(state_node_pattern, line)
      if match:
        #We see a new state node! Bubble this discovery Up!
        if not found_end_node:
          #If we never found an end node, this probably means that this edge was meant to be a self edge
          edge = (outgoing_node, outgoing_node)
          if outgoing_node == "tagNameState" and label == "Anything Else":
            #We are currently in the tag name state. Only allow "Anything Else" in the tag name if we are not in a special tag name state after the tag open state
            self.addEdgeForTags(edge, label, ["asciiLetters"])
          else:
            self.addEdgeForTags(edge, label, all_tags)

        f.undoReadLine()
        break

      if "self.emitCurrentToken()" in line:
        if "rawtext" not in outgoing_node and "script" not in outgoing_node and "rcdata" not in outgoing_node:
          #When emitting tokens not in rawtext, script, or rcdata states, we need to make sure we transition to the
          #appropriate data state depending on the tag
          end_node = "dataState"
          edge = (outgoing_node, end_node)
          self.addEdgeForTags(edge, label, other_tags)

          end_node = "rcdataState"
          edge = (outgoing_node, end_node)
          self.addEdgeForTags(edge, label, cdataElements)

          end_node = "rawtextState"
          edge = (outgoing_node, end_node)
          self.addEdgeForTags(edge, label, rcdataElements)

          found_end_node = True
        else:
          #We are emitting tokens for the rawtext, script, or rcdata states. Set tag state back to asciiletters
          #and skip the next parsing the next line
          #since we know it will tell us to go to data state anyways
          end_node = "dataState"
          edge = (outgoing_node, end_node)
          self.addEdgeForTags(edge, label, all_tags, end_tag="asciiLetters")

          found_end_node = True

          line = f.readline()
          pass

        line = f.readline();
        continue

      match = re.match(end_node_pattern, line)
      if match:
        #We see an end node! We found our edge!
        end_node = match.group(1)
        edge = (outgoing_node, end_node)
        if outgoing_node == "tagOpenState" and label == "asciiLetters":
          #If we are in the tagOpenState, this is where we can change the tag state we are in
          for tag in all_tags:
            label = tag
            self.addEdgeForTags(edge, label, all_tags, end_tag=tag)
        elif outgoing_node == "closeTagOpenState" and label == "asciiLetters":
          #If we are in the closeTagOpenState, we always change the tag state back to asciiletters
          for tag in all_tags:
            label = tag
            self.addEdgeForTags(edge, label, all_tags, end_tag="asciiLetters")

        elif "TagOpenState" in outgoing_node and label == "asciiLetters":
          #Only add edges from any tag open state to the transitioned state using tags that are equal to the current tag in the tag state
          for tag in all_tags:
            if tag is not None:
              label = tag
              self.addEdgeForTags(edge, label, [tag])
        else:
          self.addEdgeForTags(edge, label, all_tags)
        found_end_node = True

        line = f.readline();
        continue

      line = f.readline();

  def addEdgeForTags(self, edge, label, tags, end_tag=None):
    for tag in tags:
      if end_tag is None:
        edge_with_tag = ((tag, edge[0]), (tag, edge[1]))
      else:
        edge_with_tag = ((tag, edge[0]), (end_tag, edge[1])) 
      self.addEdge(edge_with_tag, label)

  def addEdge(self, edge, label):
    if self.has_edge(edge):
        new_label = self.edge_label(edge) + ", " + label
        self.set_edge_label(edge, new_label)
    else:
      try:
        self.add_edge(edge, label=label)
      except AdditionError as e:
        #Something state is not in our self. Probably random entity things though.
        #Just print error message to log and double check if we should consider entity states
        print "WARNING: " + e.message
      except TypeError:
        print "WARNING: Can't add edge" + str(edge)