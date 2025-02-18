#!/usr/bin/env python3

# /// script
# dependencies = [
#   "openai>=1.62.0",
# ]
# ///

"""
/// Example Usage

# Generate a meta prompt using command-line arguments.
# Optional arguments are marked with a ?.

uv run sfa_meta_prompt_openai_v1.py \
    --purpose "generate mermaid diagrams" \
    --instructions "generate a mermaid valid chart, use diagram type specified or default flow, use examples to understand the structure of the output" \
    --sections "examples, user-prompt" \
    --examples "create examples of 3 basic mermaid charts with <user-chart-request> and <chart-response> blocks" \
    --variables "user-prompt"

# Without optional arguments, the script will enter interactive mode.
uv run sfa_meta_prompt_openai_v1.py \
    --purpose "generate mermaid diagrams" \
    --instructions "generate a mermaid valid chart, use diagram type specified or default flow, use examples to understand the structure of the output"

# Alternatively, just run the script without any flags to enter interactive mode.
uv run sfa_meta_prompt_openai_v1.py

///
"""

import argparse
import os
import sys

import openai

META_PROMPT = """<purpose>
    You are an expert prompt engineer, capable of creating detailed and effective prompts for language models.
    
    Your task is to generate a comprehensive prompt based on the user's input structure.
    
    Follow the instructions closely to generate a new prompt template.
</purpose>

<instructions>
    <instruction>Analyze the user-input carefully, paying attention to the purpose, required sections, and variables.</instruction>
    <instruction>Create a detailed prompt that includes all specified sections and incorporates the provided variables.</instruction>
    <instruction>Use clear and concise language in the generated prompt.</instruction>
    <instruction>Ensure that the generated prompt maintains a logical flow and structure.</instruction>
    <instruction>Include placeholders for variables values in the format [[variable-name]].</instruction>
    <instruction>If a section is plural, create a nested section with three items in the singular form.</instruction>
    <instruction>The key xml blocks are purpose, instructions, sections, examples, user-prompt.
    <instruction>Purpose defines the high level goal of the prompt.</instruction>
    <instruction>Instructions are the detailed instructions for the prompt.</instruction>
    <instruction>Sections are arbitrary blocks to include in the prompt.</instruction>
    <instruction>Examples are showcases of what the output should be for the prompt. Use this to steer the structure of the output based on the user-input. This will typically be a list of examples with the expected output.</instruction>
    <instruction>Variables are placeholders for values to be substituted in the prompt.</instruction>
    <instruction>Not every section is required, but purpose and instructions are typically essential. Create the xml blocks based on the user-input.</instruction>
    <instruction>Use the examples to understand the structure of the output.</instruction>
    <instruction>Your output should be in XML format, mirroring the structure of the examples output.</instruction>
    <instruction>Exclude CDATA sections in your output.</instruction>
    <instruction>Response exclusively with the desired output, no other text.</instruction>
    <instruction>If the user-input is structured like the input-format, use it as is. If it's not, infer the purpose, sections, and variables from the user-input.</instruction>
    <instruction>The goal is to fill in the blanks and best infer the purpose, instructions, sections, and variables from the user-input. If instructions are given, use them to guide the other xml blocks.</instruction>
    <instruction>Emphasize exact XML structure and nesting. Clearly define which blocks must contain which elements to ensure a well-formed output.</instruction>
    <instruction>Ensure that each section builds logically upon the previous ones, creating a coherent narrative from purpose to instructions, sections, and examples.</instruction>
    <instruction>Use direct, simple language and avoid unnecessary complexity to make the final prompt easy to understand.</instruction>
    <instruction>After creating the full prompt, perform a final validation to confirm that all placeholders, instructions, and examples are included, properly formatted, and consistent.</instruction>
    <instruction>If examples are not requested, don't create them.</instruction>
    <instruction>If sections are not requested, don't create them.</instruction>
    <instruction>If variables are not requested, just create a section for the user-input.</instruction>
</instructions>

<input-format>
    Purpose: [main purpose of the prompt], Instructions: [list of details of how to generate the output comma sep], Sections: [list of additional sections to include, e.g., examples, user-prompt], Examples: [list of examples of the output for the prompt], Variables: [list of variables to be used in the prompt]
</input-format>

<examples>
    <example>
        <input>
            Purpose: generate mermaid diagrams. Instructions: generate a mermaid valid chart, use diagram type specified or default flow, use examples to understand the structure of the output. Sections: examples, user-prompt. Variables: user-prompt
        </input>
        <output>
<![CDATA[
You are a world-class expert at creating mermaid charts.

You follow the instructions perfectly to generate mermaid charts.

<instructions>
    <instruction>Generate valid a mermaid chart based on the user-prompt.</instruction>
    <instruction>Use the diagram type specified in the user-prompt if non-specified use a flowchart.</instruction>
    <instruction>Use the examples to understand the structure of the output.</instruction>
</instructions>

<examples>
    <example>
        <user-chart-request>
            Create a flowchart that shows A flowing to E. At C, branch out to H and I.
        </user-chart-request>
        <chart-response>
            graph LR;
                A
                B
                C
                D
                E
                H
                I
                A --> B
                A --> C
                A --> D
                C --> H
                C --> I
                D --> E
        </chart-response>
    </example>
    <example>
        <user-chart-request>
            Build a pie chart that shows the distribution of Apples: 40, Bananas: 35, Oranges: 25.
        </user-chart-request>
        <chart-response>
            pie title Distribution of Fruits
                "Apples" : 40
                "Bananas" : 35
                "Oranges" : 25
        </chart-response>
    </example>
    <example>
        <user-chart-request>
            State diagram for a traffic light. Still, Moving, Crash.
        </user-chart-request>
        <chart-response>
            stateDiagram-v2
                [*] --> Still
                Still --> [*]
                Still --> Moving
                Moving --> Still
                Moving --> Crash
                Crash --> [*]
        </chart-response>
    </example>
    <example>
        <user-chart-request>
            Create a timeline of major social media platforms from 2002 to 2006.
        </user-chart-request>
        <chart-response>
            timeline
                title History of Social Media Platforms
                2002 : LinkedIn
                2004 : Facebook
                        : Google
                2005 : Youtube
                2006 : Twitter
        </chart-response>
    </example>
    </examples>

<user-prompt>
    [[user-prompt]]
</user-prompt>

Your mermaid chart:
</output>
    </example>
    <example>
        <input>
            Purpose: review git diff to improve code quality. Instructions: Review git diff, give suggestions for improvements to the code organized in a list sorted by priority. Sections: git-diff. Variables: git-diff
        </input>
        <output>
<![CDATA[
<purpose>
    You are an expert at reviewing git diffs to improve code quality.
    You follow the instructions perfectly to review git diffs.
</purpose>

<instructions>
    <instruction>Review the git diff and provide a detailed analysis of the changes made.</instruction>
    <instruction>Give suggestions for improvements to the code organized in a list sorted by priority.</instruction>
    <instruction>Think through the changes in a wholistic manner and offer suggestions for improvements.</instruction>
</instructions>

<git-diff>
    [[git-diff]]
</git-diff>

Your review of the git diff:
]]>
        </output>
    </example>
    <example>
        <input>
            Purpose: convert user mathematical expressions into LaTeX. Instructions: Take the user-input, which is a mathematical expression in plain text, and output a properly formatted LaTeX equation. Sections: user-input. Variables: user-input
        </input>
        <output>
<![CDATA[
<purpose>
    You are a highly skilled mathematician who can transform plain text math expressions into LaTeX formatted equations.
</purpose>

<instructions>
    <instruction>Read the user-input plain text mathematical expression carefully.</instruction>
    <instruction>Convert it into a well-formatted LaTeX equation environment.</instruction>
    <instruction>Ensure the final output is wrapped in a LaTeX display math environment.</instruction>
</instructions>

<user-input>
    [[user-input]]
</user-input>

Your LaTeX equation:
]]>
        </output>
    </example>
    <example>
        <input>
            Purpose: Summarize and extract key action points from a user-provided legal contract
            Instructions: Thoroughly analyze the legal text, identify and summarize key clauses, highlight main obligations and deadlines, and provide recommended action points in list form for the user. Keep the final output simple and easy to understand, no legalese. Follow the examples.
            Sections: contract-text, summary, action-points, user-prompt
            Examples: show how to summarize major clauses from a rental agreement, a service contract, and an employment contract
            Variables: contract-text, user-prompt
        </input>
        <output>
<purpose>
    You are an expert legal advisor who specializes in summarizing complex contracts into clear, actionable insights.
    Your goal is to help the user quickly understand their contract, identify key clauses, and see recommended actions.
</purpose>

<instructions>
    <instruction>Read the user-provided contract text carefully.</instruction>
    <instruction>Identify the main clauses, obligations, timelines, and responsibilities mentioned.</instruction>
    <instruction>Summarize these points in simple, accessible language, avoiding jargon and unnecessary complexity.</instruction>
    <instruction>Highlight any deadlines or financial obligations that appear in the text.</instruction>
    <instruction>Create a list of recommended action points that the user should consider taking, based on the contract’s provisions.</instruction>
    <instruction>Keep the final output organized, starting with a structured summary of key clauses, then listing action points clearly.</instruction>
    <instruction>Use the examples to understand how to structure the summary and action points.</instruction>
</instructions>

<examples>
    <example>
        <user-contract-request>
            The following is a rental agreement for an apartment. It includes information about monthly rent, security deposit, responsibilities for maintenance, and conditions for early termination.
        </user-contract-request>
        <sample-contract-text>
            The tenant agrees to pay a monthly rent of $1,500 due on the 1st of each month. The tenant will provide a security deposit of $1,500, refundable at the end of the lease term, provided there is no damage. The tenant is responsible for routine maintenance of the property, while the landlord will handle structural repairs. Early termination requires a 30-day notice and forfeiture of half the security deposit.
        </sample-contract-text>
        <summary>
            - Monthly Rent: $1,500 due on the 1st  
            - Security Deposit: $1,500, refundable if no damage  
            - Maintenance: Tenant handles routine upkeep; Landlord handles major repairs  
            - Early Termination: 30-day notice required, tenant forfeits half of the deposit
        </summary>
        <action-points>
            1. Mark your calendar to pay rent by the 1st each month.  
            2. Keep the property clean and address routine maintenance promptly.  
            3. Consider the cost of forfeiting half the deposit if ending the lease early.
        </action-points>
    </example>

    <example>
        <user-contract-request>
            The user provides a service contract for IT support. It details response times, monthly service fees, confidentiality clauses, and conditions for termination due to non-payment.
        </user-contract-request>
        <sample-contract-text>
            The service provider will respond to support requests within 24 hours. A monthly fee of $300 is payable on the 15th of each month. All proprietary information disclosed will remain confidential. The provider may suspend services if payment is not received within 7 days of the due date.
        </sample-contract-text>
        <summary>
            - Response Time: Within 24 hours of each request  
            - Monthly Fee: $300, due on the 15th of each month  
            - Confidentiality: All shared information must be kept secret  
            - Non-Payment: Services suspended if not paid within 7 days after due date
        </summary>
        <action-points>
            1. Ensure timely payment by the 15th each month to avoid service suspension.  
            2. Log requests clearly so provider can respond within 24 hours.  
            3. Protect and do not disclose any proprietary information.
        </action-points>
    </example>

    <example>
        <user-contract-request>
            An employment contract is provided. It details annual salary, health benefits, employee responsibilities, and grounds for termination (e.g., misconduct or underperformance).
        </user-contract-request>
        <sample-contract-text>
            The employee will receive an annual salary of $60,000 paid in bi-weekly installments. The employer provides health insurance benefits effective from the 30th day of employment. The employee is expected to meet performance targets set quarterly. The employer may terminate the contract for repeated underperformance or serious misconduct.
        </sample-contract-text>
        <summary>
            - Compensation: $60,000/year, paid bi-weekly  
            - Benefits: Health insurance after 30 days  
            - Performance: Quarterly targets must be met  
            - Termination: Possible if underperformance is repeated or misconduct occurs
        </summary>
        <action-points>
            1. Track and meet performance goals each quarter.  
            2. Review the insurance coverage details after 30 days of employment.  
            3. Maintain professional conduct and address performance feedback promptly.
        </action-points>
    </example>
</examples>

<user-input>
    {{user-input}}
</user-input>
"""


def interactive_input():
    print("No command-line arguments provided. Entering interactive mode.\n")
    # Purpose (required)
    purpose = input(
        "🎯 Enter the main purpose of the prompt (required, e.g., 'generate mermaid diagrams'): "
    ).strip()
    while not purpose:
        print("Purpose is required!")
        purpose = input(
            "🎯 Enter the main purpose of the prompt (required, e.g., 'generate mermaid diagrams'): "
        ).strip()

    # Instructions (required)
    instructions = input(
        "📝 Enter the detailed instructions for generating the output (required, e.g., 'generate a mermaid valid chart, use diagram type specified or default flow, use examples to understand the structure of the output'): "
    ).strip()
    while not instructions:
        print("Instructions are required!")
        instructions = input(
            "📝 Enter the detailed instructions for generating the output (required, e.g., 'generate a mermaid valid chart, use diagram type specified or default flow, use examples to understand the structure of the output'): "
        ).strip()

    # Sections (optional)
    sections = input(
        "📑 Enter additional sections to include (optional, e.g., 'examples, user-prompt') (Press Enter to skip): "
    ).strip()

    # Examples (optional)
    examples = input(
        "💡 Enter examples for the prompt (optional, e.g., 'create examples of 3 basic mermaid charts with <user-chart-request> and <chart-response> blocks') (Press Enter to skip): "
    ).strip()

    # Variables (optional)
    variables = input(
        "🔄 Enter variables to be used in the prompt (optional, e.g., 'user-prompt') (Press Enter to skip): "
    ).strip()

    return purpose, instructions, sections, examples, variables


def main():
    # Check if any command-line arguments besides the script name were provided
    if len(sys.argv) == 1:
        purpose, instructions, sections, examples, variables = interactive_input()
    else:
        parser = argparse.ArgumentParser(
            description="Generate a meta prompt for OpenAI's o3-mini based on input structure"
        )
        parser.add_argument(
            "--purpose", type=str, required=True, help="The main purpose of the prompt"
        )
        parser.add_argument(
            "--instructions",
            type=str,
            required=True,
            help="The detailed instructions for generating the output",
        )
        parser.add_argument(
            "--sections", type=str, help="Additional sections to include (optional)"
        )
        parser.add_argument(
            "--examples", type=str, help="Examples for the prompt (optional)"
        )
        parser.add_argument(
            "--variables",
            type=str,
            help="Variables to be used in the prompt (optional)",
        )
        args = parser.parse_args()

        purpose = args.purpose
        instructions = args.instructions
        sections = args.sections if args.sections else ""
        examples = args.examples if args.examples else ""
        variables = args.variables if args.variables else ""

    # Build the concatenated input string using the input-format structure.
    input_parts = []
    input_parts.append(f"Purpose: {purpose}")
    input_parts.append(f"Instructions: {instructions}")
    if sections:
        input_parts.append(f"Sections: {sections}")
    if examples:
        input_parts.append(f"Examples: {examples}")
    if variables:
        input_parts.append(f"Variables: {variables}")

    user_input = ", ".join(input_parts)

    # Replace the placeholder with our concatenated user input.
    prompt = META_PROMPT.replace("{{user-input}}", user_input)

    # Set up OpenAI API key from the environment variable.
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable is not set")
        sys.exit(1)
    openai.api_key = openai_api_key

    try:
        # Use OpenAI's ChatCompletion API with the o3-mini model and high reasoning effort settings.
        response = openai.chat.completions.create(
            model="gpt-4o",
            #            reasoning_effort="high",
            messages=[{"role": "user", "content": prompt}],
        )
        # Output the response from the OpenAI model.
        print(response.choices[0].message.content.strip())
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
