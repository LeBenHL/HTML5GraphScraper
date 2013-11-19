HTML5GraphScraper
=================

These are scripts intended to be used to build a HTML5 Tokenizer State Graph and perform analysis on it to hopefully discover
a magic string to protect against HTML injection attacks.

HTML Graph Scraper
-----------------

html_graph_scraper.py is a script used to build the HTML5 Tokenizer State Graph, it does so by parsing the tokenizer.py file
line by line to find all the nodes and relevant edges between the nodes. This was done rather than using Coverity's state graph
or parsing the online documentation at http://www.whatwg.org/specs/web-apps/current-work/multipage/tokenization.html because the code
is more structured.

In our HTML5 graph, nodes are represented by a (html_tag, tokenizer_state) tuple where the html_tag is the current tag of the
token being parsed at the tokenizer_state is the current state of the tokenizer. This is done because HTML strings are parsed
differently depending on the tag name of the token that is being parsed. 

HTML5 String Search 1
---------------------

HTML5 String Search 2
---------------------
