import re
def route(query):
 q=query.lower(); markers=("compare","why","how does","tradeoff","difference","recommend"," and "," versus "," vs ")
 return ("complex","large","multi-part or reasoning cue") if len(re.findall(r"\w+",q))>18 or any(x in q for x in markers) else ("simple","small","short factual lookup")
def weak(answer,sources): return not answer or len(answer.strip())<20 or not sources or "I don't have enough" in answer
