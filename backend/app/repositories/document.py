class DocumentRepository:
    def __init__(self):
        self.documents:list[dict]=[]
        self.next_document_id=1

    def create(self,document_data:dict)->dict:
        new_document={
            "id":self.next_document_id,
            "title":document_data["title"],
            "department":document_data["department"],
            "content":document_data["content"]
        }

        self.documents.append(new_document)
        self.next_document_id+=1

        return new_document

    def get_all(self)->list[dict]:
        return self.documents

    def get_by_id(self,document_id:int)->dict|None:
        for document in self.documents:
            if document["id"] == document_id:
                return document

        return None

    def update(self,
               document_id:int,
               update_data:dict)->dict|None:

        document = self.get_by_id(document_id)

        if document is None:
            return None

        document.update(update_data)
        return document

    def delete(self,document_id:int)->dict|None:
        for index,document in enumerate(self.documents):
            if document["id"] == document_id:
                return self.documents.pop(index)

        return None

document_repository=DocumentRepository()