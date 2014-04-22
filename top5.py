#!/usr/bin/python

import wikipedia

pages = wikipedia.search("test", results=5)

for p in pages:
	page = wikipedia.page(title=p.title())
	print page.title
	print page.content
	print
