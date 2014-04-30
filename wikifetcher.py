#!/bin/env python2.7

from Queue import Queue
from threading import Thread
import wikipedia
from wikipedia.exceptions import WikipediaException, DisambiguationError
import time

num_worker_threads = 10

def fetch(query, limit=3, wikisum=True):    
    begin = time.time()
    titles = wikipedia.search(query, results = limit);
    
    # Get the pages with the returned titles
    #~ pages = map(get_page, titles) 
    queue = Queue()
    for i in xrange(len(titles)):
        queue.put((i, titles[i]))
    results = [None]*len(titles)
    
    def _work():
        while not queue.empty():
            i, meta = queue.get()
            # Retry 5 times
            for _ in xrange(5): 
                try:
                    if wikisum:
                        results[i] = (meta.title(), wikipedia.summary(meta.title())) #_fetch_page(meta) 
                    else:
                        results[i] = (meta.title(), wikipedia.page(meta.title()).content) #_fetch_page(meta) 
                    #~ print i, "Done"
                    queue.task_done()
                    break
                except Exception as ex:
                    print ex
                    pass
            if not results[i]:
                raise Exception("5 consequtive errors occured while fetching page.")
                
                
    
    for _ in range(num_worker_threads):
        t = Thread(target=_work)
        t.daemon = True
        t.start()
        
    queue.join()
    print "Performance: ", str(num_worker_threads)+" threads" 
    print "Time taken:", str(time.time() - begin)+" sec"
    return results
    
def _fetch_page(meta):
    try:
        page = wikipedia.page(title=meta.title())
    except DisambiguationError as e:
        # Only get the first disambiguation option for now
        page = wikipedia.page(title=e.options[0].title())
    return page



