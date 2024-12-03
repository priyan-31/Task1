import os
import json
from flask import Flask, render_template, send_file, request
from langchain_community.document_loaders import PyPDFLoader       #here the pdfloader is a class from langc lib. used to process pdf
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


app = Flask(__name__)
upload_folder = "uploads"
download_folder = "downloads"
os.makedirs(download_folder, exist_ok=True)
os.makedirs(upload_folder, exist_ok=True)

app.config["upload_folder"] = upload_folder
app.config["download_folder"] = download_folder

llm = ChatOpenAI(api_key=" ")                                 # here we pass our api key -5

class product(BaseModel):                                    # this is a functional class used to define data models --- pydantic model
    product_code: str = Field(description="product code")
    product_name: str = Field(description="Product name")    # basemodel & field?
    price: str = Field(description="Price")                  # used this to let know langchain what fields we need.
    category: str = Field(description="Category")
    stock_quantity: str = Field(description="stock quantity")    #know the diff. b/w class & the pydantic class used here    then need to convert this to a prompt -2

parser = JsonOutputParser(pydantic_object=product)           # initializes json output parser with pydaantic model  -3



def process_pdf(file_path):
    loader = PyPDFLoader(file_path)  #we load the pdf file using lc -1
    pages = loader.load()

    page_text = " ".join([page.page_content.strip() for page in pages if page.page_content])

    if not page_text:
        raise ValueError("No valid text found in the PDF.")



    prompt = PromptTemplate(                                                                # defines prompt to extract details of prod.
    template="Extract the information specified.\n{format_instructions}\n{context}",    # here we give only the context as input
    input_variables=["context"],
    partial_variables={"format_instructions": parser.get_format_instructions()}     # its a built in function so this will convert the class as a string in a way the model understands -4
    )

    chain = prompt | llm | parser             #  this  is a pipeline prompt , llm, parser -6


    result = chain.invoke({"context": pages})  # process and extract the product details
    return result


@app.route("/", methods = ["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "pdf" not in request.files:
            return "No file uploaded", 400

        file = request.files["pdf"]
        if file.filename == "":
            return "No file selected", 400

        file_path = os.path.join(app.config["upload_folder"], file.filename)        # Save the uploaded file to the uploads folder
        file.save(file_path)

        try:
            extracted_data = process_pdf(file_path)                    # Process the uploaded PDF and extract data

            json_file_path = os.path.join(app.config["download_folder"], "product_data.json")  # Save the extracted data to a JSON file
            with open(json_file_path, "w") as json_file:
                json.dump(extracted_data, json_file, indent=4)
           
            return send_file(json_file_path, as_attachment=True)        # Provide the JSON file for download

        except Exception as e:
            return f"Error processing PDF: {e}", 500

    return render_template("index.html")            # Render the file upload form for GET requests

if __name__ == "__main__":
    app.run(debug=True)
