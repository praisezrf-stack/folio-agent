from ..folioAgent.llm.gateway import create_model,get_embedder

chat = create_model()
emb = get_embedder()

def main():
    res = chat.invoke('通过了吗？')
    emb_res = emb.embed_query('你好')
    
    print(res.content,end="\n\n")
    print(len(emb_res))

if __name__=="__main__":
    main()