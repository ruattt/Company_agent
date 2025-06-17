# memory_retrieval.py
#从图数据库中检索记忆信息的模块，并生成string格式的记忆信息
#（实际流程是只用了实体，然后查找出该实体3跳以内的所有关系一并发送给大模型）
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD  # 导入配置
from typing import Optional, List
from question_processing import QuestionAnalyzer
from response_generation import ResponseGenerator
import asyncio
import textwrap
import logging


class MemoryRetriever:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        self.question_analyzer = QuestionAnalyzer()
        self.response_generator = ResponseGenerator()
        self.logger = logging.getLogger(__name__)

    """
    去除前导空白：将多行字符串中每一行的共同前导空白（如空格、制表符）去除，使文本更紧凑。
    格式化 SQL 查询语句：在代码中用于美化缩进的多行 Cypher 查询语句，
    使其可以嵌套在 Python 代码中并保持可读性，同时避免额外的缩进影响实际查询内容。
    """
    async def _query_graph(self, entities: List[str], relations: List[str]) -> Optional[str]:
        """改进的APOC查询方法"""
        query = textwrap.dedent("""
        UNWIND $entities AS searchName
        MATCH (n {name: searchName})
        WITH collect(n) AS startNodes
        CALL apoc.path.subgraphNodes(startNodes, {
            relationshipFilter: ">|<",
            minLevel: 1,
            maxLevel: 3
        }) YIELD node
        WITH DISTINCT node
        MATCH (node)-[r]->(related)
        RETURN 
            node.name AS start_name,
            node.type AS start_type,
            type(r) AS relationship,
            related.name AS end_name,
            related.type AS end_type,
            r.create_time AS time
        UNION
        MATCH (related)-[r]->(node)
        RETURN 
            related.name AS start_name,
            related.type AS start_type,
            type(r) AS relationship,
            node.name AS end_name,
            node.type AS end_type,
            r.create_time AS time
        ORDER BY time DESC
        LIMIT 50
        """)

        try:
            with self.driver.session() as session:
                result = session.run(query, entities=entities)
                return self._format_relations(result)
        except Exception as e:
            self.logger.error(f"查询失败: {str(e)}")
            return None

    def _format_relations(self, records) -> str:
        """安全的关系格式化方法"""
        memory_facts = []
        for record in records:
            # 确保处理的是Record对象
            if not hasattr(record, 'get'):
                continue
                
            try:
                start_name = record.get("start_name", "未知实体")
                start_type = record.get("start_type", "")
                rel_type = record.get("relationship", "未知关系")
                end_name = record.get("end_name", "未知实体")
                end_type = record.get("end_type", "")
                time = record.get("time")
                
                fact = f"{start_name}({start_type}) -[{rel_type}]-> {end_name}({end_type})"
                
                if time:
                    try:
                        ts = time.to_native().strftime("%Y-%m-%d")
                        fact += f" ({ts})"
                    except:
                        pass
                        
                memory_facts.append(fact)
            except Exception as e:
                print(f"记录处理异常: {str(e)}")
        
        # 去重并限制长度
        return "\n".join(list(dict.fromkeys(memory_facts)))[:2000]

    def _format_single_relation(self, start_node, rel, end_node):
        print("\n[APOC查询原始记录]")  # 新增调试输出

        """单条关系格式化"""
        fact = {
            "from": start_node["name"],
            "rel": rel.type,
            "to": end_node["name"],
            "time": rel.get("create_time", None)
        }
        
        # 添加类型信息
        if "type" in start_node:
            fact["from_type"] = start_node["type"]
        if "type" in end_node:
            fact["to_type"] = end_node["type"]
        
        # 生成自然语言描述
        time_str = ""
        if fact["time"]:
            ts = fact["time"].to_native().strftime("%Y-%m-%d")
            time_str = f"（时间：{ts}）"
        
        return f"{fact['from']} ({fact.get('from_type','')}) "\
            f"-[{fact['rel']}]-> "\
            f"{fact['to']} ({fact.get('to_type','')}){time_str}"

    async def process_question(self, question: str, userid: str) -> str:
        # 步骤1：分析问题
        analysis = await self.question_analyzer.analyze(question, userid)
        # print(f"\n[DEBUG] 问题分析结果：{analysis}")
        # print(f"[DEBUG] 执行查询：{analysis.target_entities}")

        # 步骤2：查询图数据库
        memory_context = await self._query_graph(
            analysis.target_entities,
            analysis.possible_relations
        )
        
        if not memory_context:
            memory_context = "暂时没有相关记忆"
        # print(f"[DEBUG] 原始记忆片段：\n{memory_context}")

        # 步骤3：生成回答
        return await self.response_generator.generate(question, memory_context)
async def main_flow():
    
    test_analyzer = QuestionAnalyzer()
    test_question = "我爸的工作是什么？"
    analysis = await test_analyzer.analyze(test_question, "user123")
    print(f"\n[验证测试] 问题分析结果：")
    print(f"目标实体：{analysis.target_entities}")
    print(f"推测关系：{analysis.possible_relations}")

if __name__ == "__main__":
    # 异步执行测试
    asyncio.run(main_flow())