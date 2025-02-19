#!/usr/bin/env python3

# /// script
# dependencies = [
#   "anthropic",
#   "pydantic==2.10.6",
#   "docling==2.23.0",
# ]
# ///


import json
import os
from typing import Optional

from anthropic import Anthropic
from docling.document_converter import DocumentConverter
from pydantic import BaseModel, Field


class extract(BaseModel):
    total: Optional[float] = Field(None, description="Total amount to be paid")
    currency: Optional[str] = Field(None, description="Currency code")
    invoiceNumber: Optional[str] = Field(None, description="Invoice number")
    invoiceDate: Optional[str] = Field(None, description="Issue date (YYYY-MM-DD)")
    dueDate: Optional[str] = Field(None, description="Due date (YYYY-MM-DD)")
    companyName: Optional[str] = Field(None, description="Company name")
    companyAddress: Optional[str] = Field(None, description="Company address")


# -----------------
# | Parse the pdf to markdown with docling|
# -----------------

pdf = "test_invoice.pdf"


def parse_pdf_to_markdown(pdf: str) -> str:
    try:
        converter = DocumentConverter()
        result = converter.convert(pdf)
        text = result.document.export_to_markdown()
        return text.strip()
    except Exception as e:
        raise Exception(f"Error parsing PDF file: {str(e)}")


# -----------------
# | Extract structured data from markdown using Anthropic |
# -----------------


def extract_structured_data(markdown: str) -> extract:
    """Extract structured data from markdown using Anthropic API"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise Exception("ANTHROPIC_API_KEY environment variable not set")

    client = Anthropic(api_key=api_key)

    system_prompt = """
    You are an expert at extracting structured data from documents.
    Your task is to extract specific fields from the provided markdown document.
    Return ONLY a JSON object that matches the following schema:
    
    {
        "total": float,           # Total amount to be paid
        "currency": string,      # Currency code
        "invoiceNumber": string, # Invoice number
        "invoiceDate": string,   # Issue date (YYYY-MM-DD)
        "dueDate": string,       # Due date (YYYY-MM-DD)
        "companyName": string,   # Company name
        "companyAddress": string # Company address
    }
    
    Respond with ONLY the JSON object, no other text.
    """

    user_prompt = f"Here is the markdown document to extract from:\n\n{markdown}"

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Extract JSON from the response
            json_str = response.content[0].text
            data = json.loads(json_str)

            # Validate using pydantic v2
            validated = extract.model_validate(data)
            return validated

        except json.JSONDecodeError:
            if attempt == max_retries - 1:
                raise Exception("Failed to get valid JSON after max retries")
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"Error extracting data: {str(e)}")


def main():
    # Parse PDF to markdown
    markdown = parse_pdf_to_markdown(pdf)

    # Extract structured data
    try:
        data = extract_structured_data(markdown)
        print("\nExtracted Data:")
        print(data.model_dump_json(indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
