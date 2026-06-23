from ddgs import DDGS

def search_internet(query, max_results=5):
    try:
        results = []
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": item.get("title", ""),
                    "href": item.get("href", ""),
                    "body": item.get("body", "")
                })
        if not results:
            return "No search results found."
        text = "🌐 Internet search results:\n\n"
        for i, r in enumerate(results, start=1):
            text += f"{i}. {r['title']}\n{r['body']}\n{r['href']}\n\n"
        return text
    except Exception as error:
        print(error)
        return "Internet search failed. Please check your connection."
