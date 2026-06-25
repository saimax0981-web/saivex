import re

try:
    from ddgs import DDGS
except Exception:
    DDGS = None


def clean_topic(prompt):
    text = prompt.strip()
    phrases = [
        "create ppt about", "make ppt about", "create powerpoint about",
        "create presentation about", "generate ppt about",
        "create pdf about", "make pdf about", "generate pdf about",
        "create website about", "make website about", "build website about",
        "create website for", "make website for", "build website for",
        "search:", "about"
    ]

    low = text.lower()
    for phrase in phrases:
        if low.startswith(phrase):
            text = text[len(phrase):].strip()
            break

    return re.sub(r"\s+", " ", text) or prompt.strip()


def web_search(topic, max_results=8):
    results = []

    if DDGS:
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(topic, max_results=max_results):
                    title = r.get("title", "")
                    body = r.get("body", "")
                    href = r.get("href", "")
                    if title or body:
                        results.append({"title": title, "snippet": body, "url": href})
        except Exception as error:
            print("DDGS search failed:", error)

    if not results:
        results = [
            {
                "title": f"Overview of {topic}",
                "snippet": f"{topic} is an important subject. This output uses structured knowledge and topic context.",
                "url": ""
            },
            {
                "title": f"Key facts about {topic}",
                "snippet": "Important areas include background, timeline, concepts, applications, challenges, trends, and future scope.",
                "url": ""
            }
        ]

    return results


def generate_points(topic, section_title, source_hint):
    templates = {
        "Introduction": [
            f"{topic} is a significant topic with historical, practical, or modern importance.",
            f"It can be understood through its origin, development, major ideas, and current relevance.",
            "This section gives a clear starting point before deeper details."
        ],
        "Background and Context": [
            f"The background of {topic} helps explain why it became important.",
            "Context includes social, scientific, technological, cultural, or historical factors.",
            "Understanding context makes the later sections easier to follow."
        ],
        "Key Concepts": [
            f"The main ideas of {topic} form the foundation of the subject.",
            "Each concept connects to examples, use cases, or real-world impact.",
            "These concepts should be explained with clarity rather than repetition."
        ],
        "Important Facts": [
            f"Several facts make {topic} worth studying in detail.",
            "Important facts include timelines, contributors, features, results, or discoveries.",
            "These points help the audience remember the core message."
        ],
        "Applications": [
            f"{topic} can be applied in education, technology, society, business, or daily life.",
            "Applications show how the topic is useful beyond theory.",
            "Good examples make the output more engaging."
        ],
        "Challenges": [
            f"{topic} also has challenges that need careful understanding.",
            "Limitations may involve cost, access, accuracy, ethics, adoption, or complexity.",
            "Discussing challenges makes the output balanced and realistic."
        ],
        "Current Trends": [
            f"Recent trends show how {topic} is changing over time.",
            "Modern developments are shaped by technology, research, and public interest.",
            "Trends help connect the topic to the present day."
        ],
        "Future Scope": [
            f"The future of {topic} depends on innovation, research, and practical adoption.",
            "Future improvements may create new opportunities and solutions.",
            "This section helps the audience think beyond the current situation."
        ],
        "Conclusion": [
            f"{topic} is best understood by combining background, facts, applications, and future scope.",
            "A strong conclusion should repeat the main idea without copying earlier slides or pages.",
            "The final takeaway should be clear, memorable, and useful."
        ],
    }

    points = templates.get(section_title, [
        f"This section discusses {section_title.lower()} related to {topic}.",
        "The content should be focused, useful, and easy to understand.",
        "Examples and facts make the section stronger."
    ])

    if source_hint:
        points.append(f"Research note: {source_hint[:190].strip()}")

    return points


def make_sections(topic, sources, count=9):
    titles = [
        "Introduction",
        "Background and Context",
        "Key Concepts",
        "Important Facts",
        "Applications",
        "Challenges",
        "Current Trends",
        "Future Scope",
        "Conclusion"
    ]

    snippets = [s.get("snippet", "") for s in sources if s.get("snippet")]
    sections = []

    for i in range(count):
        title = titles[i] if i < len(titles) else f"Section {i+1}"
        source_hint = snippets[i % len(snippets)] if snippets else ""
        sections.append({
            "title": title,
            "points": generate_points(topic, title, source_hint),
            "source": sources[i % len(sources)] if sources else {}
        })

    return sections
