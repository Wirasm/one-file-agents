#!/usr/bin/env python3

# /// script
# dependencies = [
#   "anthropic>=0.45.2",
#   "rich>=13.7.0",
#   "pydantic>=2.10.6",
#   "docling>=2.23.0",
# ]
# ///

"""
/// Example Usage

# Extract structured data from PDF
uv run sfa_structured_anthropic.py -f test_invoice.pdf

///
"""

import argparse
import json
import os
import sys
from typing import List, Optional

from anthropic import Anthropic
from docling.document_converter import DocumentConverter
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel

# Initialize rich console
console = Console()


class extract(BaseModel):
    total: Optional[float] = Field(None, description="Total amount to be paid")
    currency: Optional[str] = Field(None, description="Currency code")
    invoiceNumber: Optional[str] = Field(None, description="Invoice number")
    invoiceDate: Optional[str] = Field(None, description="Issue date (YYYY-MM-DD)")
    dueDate: Optional[str] = Field(None, description="Due date (YYYY-MM-DD)")
    companyName: Optional[str] = Field(None, description="Company name")
    companyAddress: Optional[str] = Field(None, description="Company address")


def parse_pdf_to_markdown(pdf_path: str) -> str:
    """Convert PDF to markdown format"""
    try:
        console.log("[blue]Converting PDF to markdown...[/blue]")
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        text = result.document.export_to_markdown()
        console.log("[green]PDF conversion successful[/green]")
        return text.strip()
    except Exception as e:
        console.print(f"[red]Error parsing PDF file: {str(e)}[/red]")
        raise


AGENT_PROMPT = """<purpose>
    You are a world-class expert at extracting structured data from invoices.
    Your goal is to extract precise information that matches the required schema.
</purpose>

<instructions>
    <instruction>Read the entire invoice document carefully.</instruction>
    <instruction>Identify and extract each required field such as total amount, currency, invoice number, etc.</instruction>
    <instruction>Validate the data types and formats, ensuring dates are in YYYY-MM-DD format.</instruction>
    <instruction>Return the JSON object exactly as specified, with null for any missing fields.</instruction>
    <instruction>Be precise with currency codes (e.g., "USD", "EUR").</instruction>
    <instruction>Include all available address components for company addresses.</instruction>
</instructions>

<output_schema>
{
    "total": float,          # Total amount to be paid
    "currency": string,      # Currency code (e.g., USD, EUR)
    "invoiceNumber": string, # Invoice number or identifier
    "invoiceDate": string,   # Issue date in YYYY-MM-DD format
    "dueDate": string,       # Due date in YYYY-MM-DD format
    "companyName": string,   # Full legal company name
    "companyAddress": string # Complete company address
}
</output_schema>
"""


def extract_structured_data(markdown: str, reasoning: str) -> extract:
    """Extract structured data from markdown using Anthropic API"""
    try:
        console.log(f"[blue]Extracting structured data - {reasoning}[/blue]")

        # Create a new Anthropic client for this extraction
        client = Anthropic()

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            system=AGENT_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Extract structured data from this document:\n\n{markdown}",
                }
            ],
        )

        json_str = response.content[0].text
        data = json.loads(json_str)

        # Validate using pydantic
        validated = extract.model_validate(data)
        console.print(
            Panel(validated.model_dump_json(indent=2), title="Extracted Data")
        )
        return validated

    except json.JSONDecodeError as e:
        console.print(f"[red]Failed to parse JSON response: {str(e)}[/red]")
        raise
    except Exception as e:
        console.print(f"[red]Error during extraction: {str(e)}[/red]")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Extract structured data from a PDF document"
    )
    parser.add_argument(
        "-f", "--file", type=str, required=True, help="Path to the PDF file"
    )
    parser.add_argument(
        "-c", "--compute", type=int, default=10, help="Maximum number of agent loops"
    )
    args = parser.parse_args()

    if not os.path.exists(args.file):
        console.print(f"[red]Error: The file '{args.file}' was not found[/red]")
        sys.exit(1)

    # Set up Anthropic client
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if not ANTHROPIC_API_KEY:
        console.print(
            "[red]Error: ANTHROPIC_API_KEY environment variable is not set[/red]"
        )
        sys.exit(1)

    client = Anthropic()

    # Convert PDF to markdown
    try:
        markdown = parse_pdf_to_markdown(args.file)
        console.print(Panel(markdown[:200] + "...", title="Document Preview"))
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)

    # Initialize message history
    messages = [{"role": "user", "content": AGENT_PROMPT}]
    compute_iterations = 0

    try:
        # Main agent loop
        while True:
            console.rule(
                f"[yellow]Agent Loop {compute_iterations + 1}/{args.compute}[/yellow]"
            )
            compute_iterations += 1

            if compute_iterations >= args.compute:
                console.print(
                    "[yellow]Warning: Reached maximum compute loops without final extraction[/yellow]"
                )
                raise Exception(
                    f"Maximum compute loops reached: {compute_iterations}/{args.compute}"
                )

            try:
                if compute_iterations == 1:
                    messages.append({"role": "user", "content": markdown})

                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    messages=messages,
                    tools=[
                        {
                            "name": "extract_structured_data",
                            "description": "Extracts structured data from the markdown representation of an invoice.",
                            "input_schema": {
                                "type": "object",
                                "properties": {
                                    "markdown": {
                                        "type": "string",
                                        "description": "The markdown text of the invoice.",
                                    },
                                    "reasoning": {
                                        "type": "string",
                                        "description": "Explanation for why we're extracting this data",
                                    },
                                },
                                "required": ["markdown", "reasoning"],
                            },
                        }
                    ],
                    tool_choice={"type": "any"},  # Always force a tool call
                )

                # Look for tool calls in the response
                tool_calls = []
                for block in response.content:
                    if hasattr(block, "type") and block.type == "tool_use":
                        tool_calls.append(block)

                if tool_calls:
                    for tool_call in tool_calls:
                        tool_use_id = tool_call.id
                        func_name = tool_call.name
                        func_args = tool_call.input  # already a dict

                        console.print(
                            f"[blue]Tool Call:[/blue] {func_name}({json.dumps(func_args)})"
                        )
                        messages.append(
                            {"role": "assistant", "content": response.content}
                        )

                        try:
                            if func_name == "extract_structured_data":
                                result = extract_structured_data(
                                    markdown=func_args["markdown"],
                                    reasoning=func_args["reasoning"],
                                )

                                # Add the result to message history
                                messages.append(
                                    {
                                        "role": "user",
                                        "content": [
                                            {
                                                "type": "tool_result",
                                                "tool_use_id": tool_use_id,
                                                "content": result.model_dump_json(
                                                    indent=2
                                                ),
                                            }
                                        ],
                                    }
                                )

                                # If we have essential fields, we're done
                                if result.total and result.invoiceNumber:
                                    console.print("\n[green]Final Results:[/green]")
                                    console.print(
                                        Panel(
                                            result.model_dump_json(indent=2),
                                            title="Extracted Data",
                                        )
                                    )
                                    return
                            else:
                                raise Exception(f"Unknown tool call: {func_name}")

                        except Exception as e:
                            error_msg = f"Error executing {func_name}: {str(e)}"
                            console.print(f"[red]{error_msg}[/red]")
                            messages.append(
                                {
                                    "role": "tool",
                                    "content": error_msg,
                                    "tool_call_id": tool_call.id,
                                }
                            )
                            continue

                else:
                    raise Exception(
                        "No tool calls found in response - should never happen"
                    )

            except Exception as e:
                console.print(f"[red]Error in agent loop: {str(e)}[/red]")
                raise e

    finally:
        console.print("[green]Process completed successfully![/green]")


if __name__ == "__main__":
    main()
