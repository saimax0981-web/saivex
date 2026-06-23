class BrainContext:
    def __init__(self):
        self.last_tool = "chat"
        self.last_topic = ""
        self.last_file = ""
        self.last_image = ""
        self.last_project = "Saivex"

    def update(self, tool, topic=""):
        self.last_tool = tool
        if topic:
            self.last_topic = topic

    def summary(self):
        return f"""Current context:
Last tool: {self.last_tool}
Last topic: {self.last_topic}
Last project: {self.last_project}
"""
