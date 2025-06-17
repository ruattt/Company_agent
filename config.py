import os

# Neo4j 配置
NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "12345678"

# OpenAI 配置
OPENAI_API_KEY = "sk-f820ab05bf104fb09c78be28f108bdf7"
OPENAI_API_BASE = "https://api.deepseek.com"

# 设置环境变量（可选）
os.environ["NEO4J_URI"] = NEO4J_URI
os.environ["NEO4J_USERNAME"] = NEO4J_USERNAME
os.environ["NEO4J_PASSWORD"] = NEO4J_PASSWORD
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE