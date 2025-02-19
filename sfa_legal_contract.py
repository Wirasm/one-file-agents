#!/usr/bin/env python3

# /// script
# dependencies = [
#   "anthropic>=0.45.2",
#   "rich>=13.7.0",
#   "docling",  # or replace with docling if available
# ]
# ///

"""
Example Usage:

This agent processes a private insurance contract (in PDF format), extracts its text,
and then uses an LLM to summarize and extract key action points.

You must set your Anthropic API key:
export ANTHROPIC_API_KEY="your-anthropic-api-key"

Run the agent with:
uv run insurance_contract_agent.py --contract "path/to/insurance_contract.pdf" --prompt "Please summarize the contract and list recommended action points."
"""

import argparse
import json
import os
import sys
from typing import List

from anthropic import Anthropic
from docling.document_converter import DocumentConverter
from rich.console import Console
from rich.panel import Panel

console = Console()


# -----------------------------------------------------------------------------
# PDF Parsing Function (using DocLing)
# -----------------------------------------------------------------------------
def parse_contract_pdf(pdf_path: str) -> str:
    """
    Extracts text from a PDF file located at pdf_path using DocLing.
    Utilizes the DocumentConverter's convert() method and exports to markdown.
    return the result so that it can be used by the agent
    use the document.pdf from the root dir of the project
    """
    pdf_path = "document.pdf"
    try:
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        text = result.document.export_to_markdown()
        # Print the parsed text for debugging
        console.print("\n[blue]Parsed Document Text:[/blue]\n")
        console.print(text)
        return text.strip()
    except Exception as e:
        raise Exception(f"Error parsing PDF file: {str(e)}")


# -----------------------------------------------------------------------------
# Agent Prompt (Exact XML structure as provided)
# -----------------------------------------------------------------------------
AGENT_PROMPT = r"""<purpose>
  You are an expert legal advisor specializing in private insurance contracts. Your goal is to help the user quickly understand the insurance policy, identify key coverage details, obligations, premiums, and deductibles, and see recommended actions.
</purpose>

<instructions>
  <instruction>Read the user-provided insurance contract text carefully.</instruction>
  <instruction>Identify the primary clauses, coverage details, premium obligations, deductibles, and any timelines or conditions mentioned.</instruction>
  <instruction>Summarize these points in simple, accessible language, avoiding jargon and unnecessary complexity.</instruction>
  <instruction>Highlight any important deadlines, premium due dates, or financial obligations.</instruction>
  <instruction>Create a list of recommended action points that the user should consider taking, based on the contract's provisions.</instruction>
  <instruction>Keep the final output organized, starting with a structured summary of key clauses, then listing action points clearly.</instruction>
  <instruction>Use the examples to understand how to structure the summary and action points.</instruction>
</instructions>

<examples>
  <example>
    <user-contract-request>
      The following is a private health insurance policy from InsureCo. It includes details about monthly premiums, deductible amounts, coverage limits, and out-of-pocket maximums.
    </user-contract-request>
    <sample-contract-text>
      The policyholder agrees to pay a monthly premium of $250, with an annual deductible of $1,000. The policy covers hospitalization, outpatient services, and emergency care up to a maximum of $100,000 per year. Any expenses exceeding the deductible are subject to a 20% coinsurance, and there is an out-of-pocket limit of $5,000 per annum.
    </sample-contract-text>
    <summary>
      - Monthly Premium: $250  
      - Annual Deductible: $1,000  
      - Coverage: Hospitalization, outpatient services, and emergency care up to $100,000/year  
      - Coinsurance: 20% after deductible with a $5,000 out-of-pocket limit
    </summary>
    <action-points>
      1. Ensure timely monthly premium payments.  
      2. Monitor deductible and out-of-pocket expenses throughout the year.  
      3. Review the details of coverage and coinsurance with your provider.
    </action-points>
  </example>
  <example>
    <user-contract-request>
      The following is an insurance broker agreement outlining services for advising clients on various insurance products. It details commission structures, consultation fees, and obligations to disclose conflicts of interest.
    </user-contract-request>
    <sample-contract-text>
      The broker will provide advisory services and earn a commission of 5% on the premiums of the policies sold. In addition, there is a consultation fee of $100 per client meeting. The broker must fully disclose any conflicts of interest and adhere to impartial advice guidelines.
    </sample-contract-text>
    <summary>
      - Commission: 5% on policy premiums  
      - Consultation Fee: $100 per meeting  
      - Disclosure: Full disclosure of conflicts of interest required
    </summary>
    <action-points>
      1. Confirm commission structures and fee arrangements.  
      2. Verify that all potential conflicts of interest are transparently disclosed.  
      3. Clarify the scope of advisory services with the broker.
    </action-points>
  </example>
  <example>
    <user-contract-request>
      The following is an agreement for an insurance pool where multiple companies share risk. It includes premium contribution details, claims distribution mechanisms, and governance structures.
    </user-contract-request>
    <sample-contract-text>
      Members of the insurance pool agree to contribute a fixed premium of $500 per quarter. In the event of a claim, losses will be distributed among members based on their contribution percentage. The pool is managed by an elected board, and all members must comply with standardized underwriting guidelines.
    </sample-contract-text>
    <summary>
      - Quarterly Premium: $500 per member  
      - Claims Sharing: Proportional distribution based on contributions  
      - Governance: Managed by an elected board with standardized guidelines
    </summary>
    <action-points>
      1. Verify your premium contributions and review the claims sharing formula.  
      2. Understand your responsibilities within the insurance pool.  
      3. Review the governance structure and ensure compliance with underwriting guidelines.
    </action-points>
  </example>
</examples>

<contract-text>
  [[contract-text]]
</contract-text>
<user-prompt>
  [[user-prompt]]
</user-prompt>
Your contract summary and action points:
"""


# -----------------------------------------------------------------------------
# Tool Functions for Contract Extraction
# -----------------------------------------------------------------------------
def summarize_contract(reasoning: str, contract_text: str, user_prompt: str) -> str:
    """
    Simulates summarizing the contract text and extracting key clauses and action points.
    In production, this could be replaced with an LLM call.
    """
    summary = (
        "- Key Clauses: Premium, Deductible, Coverage, Coinsurance\n"
        "- Premium: Look for monthly/annual amounts\n"
        "- Deductible: Identify amounts and conditions\n"
        "- Coverage: Which risks and limits\n"
        "- Other: Note deadlines and obligations"
    )
    action_points = (
        "1. Confirm your premium schedule.\n"
        "2. Review deductible and out-of-pocket limits.\n"
        "3. Verify coverage details with your insurer.\n"
        "4. Note any deadlines or special conditions."
    )
    output = f"Summary:\n{summary}\n\nAction Points:\n{action_points}\n\nUser Prompt: {user_prompt}"
    return output


def confirm_output(reasoning: str, extracted_output: str) -> str:
    """
    Simulates a final confirmation step. In production, this might involve a human review.
    """
    confirmation = f"Final Confirmed Output:\n{extracted_output}\n\n(Confirmed by automated review)"
    return confirmation


# -----------------------------------------------------------------------------
# Main Agent Loop
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Insurance Contract Summarization Agent"
    )
    parser.add_argument(
        "--contract", required=True, help="Path to the insurance contract PDF file"
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="User prompt regarding what to extract from the contract",
    )
    parser.add_argument(
        "-c", "--compute", type=int, default=10, help="Maximum number of agent loops"
    )
    args = parser.parse_args()

    try:
        contract_text = parse_contract_pdf(args.contract)
    except Exception as e:
        console.print(f"[red]Error parsing contract PDF: {str(e)}[/red]")
        sys.exit(1)

    user_prompt = args.prompt
    full_prompt = AGENT_PROMPT.replace("[[contract-text]]", contract_text).replace(
        "[[user-prompt]]", user_prompt
    )
    messages = [{"role": "user", "content": full_prompt}]
    compute_iterations = 0
    last_result = None

    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if not ANTHROPIC_API_KEY:
        console.print(
            "[red]Error: ANTHROPIC_API_KEY environment variable is not set[/red]"
        )
        sys.exit(1)
    client = Anthropic()

    # Pass tool_choice as a dictionary (per current API requirement)
    while True:
        console.rule(
            f"[yellow]Agent Loop {compute_iterations + 1}/{args.compute}[/yellow]"
        )
        compute_iterations += 1
        if compute_iterations >= args.compute:
            console.print("[yellow]Reached maximum compute loops. Exiting.[/yellow]")
            break

        try:
            if compute_iterations == 1:
                messages.append({"role": "user", "content": args.prompt})
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=messages,
                tools=[
                    {
                        "name": "summarize_contract",
                        "description": "Summarizes the insurance contract text and extracts key clauses and action points based on the user prompt.",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "reasoning": {
                                    "type": "string",
                                    "description": "Why you are summarizing the contract.",
                                },
                                "contract_text": {
                                    "type": "string",
                                    "description": "The full text of the insurance contract.",
                                },
                                "user_prompt": {
                                    "type": "string",
                                    "description": "The user's request regarding the contract.",
                                },
                            },
                            "required": ["reasoning", "contract_text", "user_prompt"],
                        },
                    },
                    {
                        "name": "confirm_output",
                        "description": "Confirms the final extracted summary and action points before sending them to the user.",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "reasoning": {
                                    "type": "string",
                                    "description": "Why you are confirming the output.",
                                },
                                "extracted_output": {
                                    "type": "string",
                                    "description": "The summary and action points extracted from the contract.",
                                },
                            },
                            "required": ["reasoning", "extracted_output"],
                        },
                    },
                ],
                tool_choice={"type": "any"},  # Passing as a dictionary
            )

            tool_calls = [
                block
                for block in response.content
                if hasattr(block, "type") and block.type == "tool_use"
            ]

            if tool_calls:
                for tool_call in tool_calls:
                    tool_use_id = tool_call.id
                    func_name = tool_call.name
                    func_args = tool_call.input  # already a dict
                    console.print(
                        f"[blue]Tool Call:[/blue] {func_name}({json.dumps(func_args)})"
                    )
                    messages.append({"role": "assistant", "content": response.content})
                    try:
                        if func_name == "summarize_contract":
                            result = summarize_contract(
                                reasoning=func_args["reasoning"],
                                contract_text=func_args["contract_text"],
                                user_prompt=func_args["user_prompt"],
                            )
                        elif func_name == "confirm_output":
                            result = confirm_output(
                                reasoning=func_args["reasoning"],
                                extracted_output=func_args["extracted_output"],
                            )
                        else:
                            raise Exception(f"Unknown tool call: {func_name}")

                        console.print(
                            f"[blue]Tool Call Result:[/blue] {func_name}(...) ->\n{result}"
                        )
                        messages.append(
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": tool_use_id,
                                        "content": str(result),
                                    }
                                ],
                            }
                        )
                        # If confirm_output was called, assume final output reached.
                        if func_name == "confirm_output":
                            console.print(
                                Panel(
                                    result,
                                    title="Final Contract Summary and Action Points",
                                )
                            )
                            return
                        # Check for repetition: if result hasn't changed, exit.
                        if (
                            last_result is not None
                            and result.strip() == last_result.strip()
                        ):
                            console.print(
                                "[green]No further constructive changes detected. Final output reached.[/green]"
                            )
                            console.print(
                                Panel(
                                    result,
                                    title="Final Contract Summary and Action Points",
                                )
                            )
                            return
                        last_result = result
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
                console.print(
                    "[yellow]No tool calls found in response. Exiting loop.[/yellow]"
                )
                break

        except Exception as e:
            console.print(f"[red]Error in agent loop: {str(e)}[/red]")
            break


if __name__ == "__main__":
    main()
