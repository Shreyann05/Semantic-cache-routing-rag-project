import time
from app.cache import SemanticCache
from app.router import route,weak
from app.metrics import cost
from app.rag import LiteLLM
def test_cache_hit_and_version(tmp_path):
 c=SemanticCache(tmp_path/"c.json",.5,60); c.put("refund policy","answer",[{"id":"refund"}],"v1")
 assert c.get("refund policy","v1")[0]
 assert c.get("refund policy","v2")[0] is None
def test_paraphrase_and_near_miss(tmp_path):
 c=SemanticCache(tmp_path/"c.json",.8,60); c.put("What is the refund policy?","answer",[{"id":"refund"}],"v1")
 assert c.get("What is the company refund policy?","v1")[0]
 assert c.get("How long is shipping?","v1")[0] is None
def test_cache_ttl(tmp_path):
 c=SemanticCache(tmp_path/"c.json",.5,-1); c.put("refund","answer",[{"id":"x"}],"v1")
 assert c.get("refund","v1")[0] is None
def test_router_and_quality():
 assert route("What is shipping?")[1]=="small"
 assert route("Compare refunds and cancellation policies")[1]=="large"
 assert weak("",[]) is True
def test_cost():
 assert cost("x",1000000,1000000,{"x":(1,2)})==3
def test_litellm_groq_adapter_uses_usage_without_network():
 class Usage:
  prompt_tokens=17
  completion_tokens=9
 class Message:
  content="Grounded answer"
 class Choice:
  message=Message()
 class Response:
  choices=[Choice()]
  usage=Usage()
 calls=[]
 def completion(**kwargs):
  calls.append(kwargs)
  return Response()
 llm=LiteLLM("test-key",completion=completion)
 assert llm.answer("What is refunded?",[{"id":"refund","text":"Refunds are allowed."}],"groq/openai/gpt-oss-20b")==("Grounded answer",17,9)
 assert calls[0]["model"]=="groq/openai/gpt-oss-20b"
 assert calls[0]["api_key"]=="test-key"
def test_groq_adapter_rejects_missing_key():
 import pytest
 with pytest.raises(RuntimeError,match="GROQ_API_KEY"):
  LiteLLM(None).answer("q",[],"groq/openai/gpt-oss-20b")
