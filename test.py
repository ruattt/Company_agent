import pyttsx3  # 导入语音合成库
from neo4j import GraphDatabase

# 列出所有可用的语音类型
# engine = pyttsx3.init()
# voices = engine.getProperty('voices')
# for index, voice in enumerate(voices):
#     print(f"语音索引：{index}")
#     print(f"语音名称：{voice.name}")
#     print(f"语音ID：{voice.id}")
#     print(f"语音语言：{voice.languages}\n")

class HelloWorldExample:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def print_greeting(self, message):
        with self.driver.session() as session:
            greeting = session.execute_write(self._create_and_return_greeting, message)
            print(greeting)

    @staticmethod
    def _create_and_return_greeting(tx, message):
        result = tx.run("CREATE (a:Greeting) "
        "SET a.message = $message "
        "RETURN a.message + ', from node ' + elementId(a)", message=message)
        return result.single()[0]

if __name__ == "__main__":
    greeter = HelloWorldExample("bolt://localhost:7687", "neo4j", "12345678")
    greeter.print_greeting("hello, world")
    greeter.close()