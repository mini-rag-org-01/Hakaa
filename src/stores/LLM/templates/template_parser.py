import os 

class TemplsteParser:

    def __init__(self, lnaguage: str=None, default_language='en'):
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.default_language = default_language
        self.lnaguage = None

        self.set_language(lnaguage)

    def set_language(self,language:str):
        if not language:
            self.lnaguage = self.default_language

        language_path = os.path.join(self.current_path,"locales", language)
        if os.path.exists(language_path):
            self.lnaguage = language

        else: 
            self.lnaguage = self.default_language

    def get(self, group:str, key:str, vars: dict={}):
        if not group and key:
            return None
        group_path = os.path.join(self.current_path,"locales", self.lnaguage,f"{group}.py")
        targeted_language = self.lnaguage

        if not os.path.exists(group_path):
            group_path = os.path.join(self.current_path,"locales", self.default_language, f"{group}.py")
            targeted_language = self.default_language

        if not os.path.exists(group_path):
            return None
        
        # Now we acccess to th target file 
        module = __import__(f"stores.LLM.templates.locales.{targeted_language}.{group}", fromlist=[group])

        if not module:
            return None
        key_attribute = getattr(module,key)

        return key_attribute.substitute(vars)