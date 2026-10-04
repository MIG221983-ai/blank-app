import requests
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineListItem
from kivy.clock import Clock

PROJECT_ID = "articuli-default-rtdb"
FIREBASE_URL = f"https://{PROJECT_ID}.europe-west1.firebasedatabase.app/products.json"

KV = '''
MDBoxLayout:
    orientation: 'vertical'
    spacing: "10dp"
    padding: "10dp"

    MDTopAppBar:
        title: "База Артикулов"
        elevation: 4

    MDTextField:
        id: search_field
        hint_text: "Начните вводить или наговорите товар..."
        mode: "rectangle"
        on_text: app.filter_products(self.text)
        size_hint_y: None
        height: "52dp"

    ScrollView:
        MDList:
            id: container_list
'''

class ArticleApp(MDApp):
    products_db = {} 

    def build(self):
        self.theme_cls.primary_palette = "Teal"
        return Builder.load_string(KV)

    def on_start(self):
        self.load_from_cloud()
        Clock.schedule_interval(self.load_from_cloud, 10)

    def update_list(self, items_dict):
        self.root.ids.container_list.clear_widgets()
        if items_dict:
            for name, data in items_dict.items():
                article = data.get("article", data) if isinstance(data, dict) else data
                item = OneLineListItem(text=f"{name}  ➔  {article}")
                self.root.ids.container_list.add_widget(item)

    def filter_products(self, text):
        if not text:
            self.update_list(self.products_db)
            return
        filtered = {k: v for k, v in products_db.items() if text.lower() in k.lower()}
        self.update_list(filtered)

    def load_from_cloud(self, *args):
        try:
            response = requests.get(FIREBASE_URL, timeout=3)
            if response.status_code == 200 and response.json():
                self.products_db.update(response.json())
                self.filter_products(self.root.ids.search_field.text)
        except:
            pass

if __name__ == '__main__':
    ArticleApp().run()
