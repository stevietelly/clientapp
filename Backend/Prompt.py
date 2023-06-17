from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.vectorstores import Chroma
from langchain.llms import GPT4All, LlamaCpp
import os
import argparse
import time

load_dotenv()

embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME")
model_type = os.environ.get('MODEL_TYPE')
model_path = os.environ.get('MODEL_PATH')
model_n_ctx = os.environ.get('MODEL_N_CTX')
model_n_batch = int(os.environ.get('MODEL_N_BATCH',8))
target_source_chunks = int(os.environ.get('TARGET_SOURCE_CHUNKS',4))

from Backend.constants import CHROMA_SETTINGS

class Prompt :
    def __init__(self, persist_directory: str, hide_source: bool = False, mute_stream: bool = False):
        self.persist_directory = persist_directory
        self.hide_source = hide_source
        self.mute_stream = mute_stream
        CHROMA_SETTINGS.persist_directory = persist_directory
        self.qa = None
    def Process(self):
        try:
            self._process()
        except Exception as error:
            return False, error
    
    def _process(self):
        embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)
        db = Chroma(persist_directory=self.persist_directory, embedding_function=embeddings, client_settings=CHROMA_SETTINGS)
        retriever = db.as_retriever(search_kwargs={"k": target_source_chunks})
        callbacks = callbacks = [] if self.mute_stream else [StreamingStdOutCallbackHandler()]
        # Prepare the LLM
        match model_type:
            case "LlamaCpp":
                llm = LlamaCpp(model_path=model_path, n_ctx=model_n_ctx, n_batch=model_n_batch, callbacks=callbacks, verbose=False)
            case "GPT4All":
                llm = GPT4All(model=model_path, n_ctx=model_n_ctx, backend='gptj', n_batch=model_n_batch, callbacks=callbacks, verbose=False)
            case _default:
                print(f"Model {model_type} not supported!")
                exit;
        self.qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents= not self.hide_source)
        
    
    def Query(self, query: str):
        # Get the answer from the chain
        start = time.time()
        res = self.qa(query)
        answer, docs = res['result'], [] if self.hide_source else res['source_documents']
        end = time.time()

        return {"answer": answer, "docs": docs, "start": start, "end": end, "time": round(end - start, 2)}

