# penguin_template.py
class Penguin:
    def __init__(self, name: str, image_url: str):
        self.name = name
        self.image_url = image_url

    def spawn_message(self):
        return f"A {self.name} penguin has appeared! Type `pen` to catch it!"
