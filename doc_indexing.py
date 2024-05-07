import os
from dotenv import load_dotenv
import math
import numpy as np
import copy

# Load environment variables from .env file
load_dotenv()

from marqo import Client

mq = Client(url=os.getenv("MARQO_URL"))


def read_files(filenames: list) -> list[dict]:
    # reads a json file
    data=[]
    for filename in filenames:
        with open(filename, 'r', encoding='utf-8') as f:
            d = dict()
            d['page_content']=f.read()
            d['title']=filename
            data.append(d)
    return data



def split_big_docs(data, field='page_content', char_len=1024):
    # there are some large documents which can cause issues for some users
    new_data = []
    for dat in data:

        page_content = dat[field]
        N = len(page_content)

        if N >= char_len:
            n_chunks = math.ceil(N / char_len)
            new_page_content = np.array_split(list(page_content), n_chunks)

            for _page_content in new_page_content:
                new_dat = copy.deepcopy(dat)
                new_dat[field] = ''.join(_page_content)
                new_data.append(new_dat)
        else:
            new_data.append(dat)
    return new_data
        
def main():
    dataset_path = ["./data/book.txt",]
    # get the data
    data = read_files(dataset_path)
    # clean up the title
    data = [d for d in data]
    data = split_big_docs(data)
    print(f"loaded data with {len(data)} entries")

    index_name = os.getenv("MARQO_INDEX_NAME")
    
    # setup the client

    try:
        mq.delete_index(index_name)
    except:
        pass

    mq.create_index(index_name, model="onnx/all_datasets_v4_MiniLM-L6")

    mq.index(index_name).add_documents(
        data, client_batch_size=50, tensor_fields=["page_content"]
    )

if __name__ == '__main__':
  main()
