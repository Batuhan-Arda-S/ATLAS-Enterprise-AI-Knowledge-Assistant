class ChunkingService:

    def split_text(self,text:str,chunk_size:int=500,overlap:int=0)->list[str]:

        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        if overlap<0:
            raise ValueError("overlap can not be negative")

        if overlap>=chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        chunks = []

        step=chunk_size-overlap

        for start in range(0,len(text),step):
            end=start+chunk_size

            chunk=text[start:end]
            chunks.append(chunk)

            if end>=len(text):
                break

        return chunks


    def split_text_smart(self,text:str,chunk_size:int=500)->list[str]:

        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        chunks = []
        start=0

        while start<len(text):

            while start<len(text) and text[start].isspace():
                start+=1

            if start>=len(text):
                break

            end=min(start+chunk_size,len(text))

            if end<len(text):
                window=text[start:end]

                separators=("\n\n","\n",". ","? ","! "," ")

                for separator in separators:
                    position=window.rfind(separator)

                    if position>0:
                        end=start+position

                        if separator in (". ", "? ", "! "):
                            end += 1

                        break

            chunk=text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            start=end

        return chunks


chunking_service=ChunkingService()