import pypdf
import json

def inspect():
    path = "data/reference_tenders/01_CAG_Manpower_Hiring_BidDoc_GEM_2021_B_1128240.pdf"
    reader = pypdf.PdfReader(path)
    pages = []
    for i, p in enumerate(reader.pages):
        text = p.extract_text() or ""
        pages.append({"page": i+1, "length": len(text), "content": text})
    
    with open("data/reference_tenders/cag_tender_extracted.json", "w", encoding="utf-8") as f:
        json.dump(pages, f, indent=2)
    print("Extracted", len(pages), "pages")

if __name__ == "__main__":
    inspect()
