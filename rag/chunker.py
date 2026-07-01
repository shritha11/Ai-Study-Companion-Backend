from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text: str):
    """
    Split extracted PDF text into overlapping chunks. 
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800, 
        chunk_overlap=150, 
        separators=[
            "\n\n", 
            "\n",
            ". ", 
            " ", 
            ""
        ],
    )

    return splitter.split_text(text)