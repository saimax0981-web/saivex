from web_search import search_web

results = search_web("latest AI news")

for r in results:
    print(r["title"])
    print(r["link"])
    print()