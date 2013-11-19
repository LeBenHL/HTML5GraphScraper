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

html5_string_search.py is a script used to find a magic string such that no matter what state the HTML tokenizer begins in, when the tokenizer parses this magic
string, it returns back to the Data State. In this file, we only consider initializing the tokenizer at states only reachable from the Data State
and finding a common string such that we return the tokenizer to the data state.

We find this common string by generating all possible strings of size 1 and seeing if all the ending states after parsing the string are the same.
If so, then we have found our magic string! We find the ending states my going through our HTML5 Tokenizer Graph generated above and continue the search
by then considering all possible strings of size 2 and then size 3 and then so on and so on. As you can see, this is quite a brute force search and although we 
consolidate characters as much as possible by representing space characters and ASCII characters all the same, there is still about 20 characters in our HTML5 character space.

HTML5 String Search 2
---------------------

This is a second method of attempting to find the magic string as described in the above section using Warren's method.

We find this magic string instead by analyzing the reverse graph of the HTML5 Tokenizer graph. We first initialize our search 
by just considering the Data State node. Then we look at all nodes reachable from the graph if traversed an edge labeled with
some character c. What this gives us is all nodes that will reach the dataState in the original graph if they traversed the edge labeled
with character c. We continue expanding this search until we are able to find a list of edge labels such that in the reverse graph, we have touched 
all possible nodes and thus, we have found a HTML5 String such that in the original graph, every node will end up in the Data State Node when 
parsing and traversing that HTML5 String.

This is a bit faster than method 1 as it cuts our search space quite significantly but I still don't think it's fast enough when considering
such a huge state machine.
