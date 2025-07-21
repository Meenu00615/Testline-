#!/usr/bin/env python
# coding: utf-8

# In[2]:


pip install pymupdf pdfplumber pillow


# In[4]:


import fitz
import pdfplumber
import json
import os
from PIL import Image

def extract_pdf_content(pdf_path, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
    
    pdf_content = {
        "metadata": {},
        "pages": []
    }
    
    with fitz.open(pdf_path) as pdf:
        pdf_content["metadata"] = {
            "title": pdf.metadata.get("title", ""),
            "author": pdf.metadata.get("author", ""),
            "pages": len(pdf)
        }
        
        for page_num in range(len(pdf)):
            page = pdf.load_page(page_num)
            page_content = {
                "page_number": page_num + 1,
                "text": "",
                "images": [],
                "questions": []
            }
            
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = pdf.extract_image(xref)
                image_bytes = base_image["image"]
                
                image_ext = base_image["ext"]
                image_filename = f"page{page_num+1}_image{img_index+1}.{image_ext}"
                image_path = os.path.join(output_dir, "images", image_filename)
                
                with open(image_path, "wb") as image_file:
                    image_file.write(image_bytes)
                
                page_content["images"].append({
                    "path": image_path,
                    "width": base_image["width"],
                    "height": base_image["height"]
                })
            
            pdf_content["pages"].append(page_content)
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            pdf_content["pages"][page_num]["text"] = text
            
            questions = []
            lines = text.split('\n')
            
            current_question = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line[0].isdigit() and '.' in line:
                    if current_question:
                        questions.append(current_question)
                    question_parts = line.split(']') if ']' in line else line.split('.')
                    if len(question_parts) > 1:
                        question_text = question_parts[1].strip()
                    else:
                        question_text = line
                    current_question = {
                        "question": question_text,
                        "options": [],
                        "images": []
                    }
                elif line.startswith('[A]') or line.startswith('A)'):
                    if current_question:
                        current_question["options"].append(line)
                else:
                    pass
            
            if current_question:
                questions.append(current_question)
            
            pdf_content["pages"][page_num]["questions"] = questions
    
    json_path = os.path.join(output_dir, "extracted_content.json")
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(pdf_content, json_file, indent=2, ensure_ascii=False)
    
    return pdf_content

if __name__ == "__main__":
    pdf_path = "IMO class 1 Maths Olympiad Sample Paper 1 for the year 2024-25.pdf"
    extracted_content = extract_pdf_content(pdf_path)
    print("PDF content extraction completed. Results saved in 'output' directory.")

