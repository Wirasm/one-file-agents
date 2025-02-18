#!/usr/bin/env python3
# /// script
# dependencies = [
#   "openrouter>=1.0.0",
#   "rich>=13.7.0",
#   "pydantic>=2.0.0",
# ]
# ///

import argparse
import json
import os
import subprocess
import sys
from typing import List

import openrouter

# Using OpenRouter's official Python SDK for third-party integration
# For information about using third-party SDKs and frameworks with OpenRouter, please see our frameworks documentation.
try:
    from openrouter import pydantic_function_tool
except ImportError:
    def pydantic_function_tool(model):
        return model
from pydantic import BaseModel, Field, ValidationError
from rich.console import Console
from rich.panel import Panel

# Initialize rich console
console = Console()


# Create our list of function tools from our pydantic models
class ListTablesArgs(BaseModel):
    reasoning: str = Field(
        ..., description="Explanation for listing tables relative to the user request"
    )


class DescribeTableArgs(BaseModel):
    reasoning: str = Field(..., description="Reason why the table schema is needed")
    table_name: str = Field(..., description="Name of the table to describe")


class SampleTableArgs(BaseModel):
    reasoning: str = Field(..., description="Explanation for sampling the table")
    table_name: str = Field(..., description="Name of the table to sample")
    row_sample_size: int = Field(
        ..., description="Number of rows to sample (aim for 3-5 rows)"
    )


class RunTestSQLQuery(BaseModel):
    reasoning: str = Field(..., description="Reason for testing this query")
    sql_query: str = Field(..., description="The SQL query to test")


class RunFinalSQLQuery(BaseModel):
    reasoning: str = Field(
        ...,
        description="Final explanation of how this query satisfies the user request",
    )
    sql_query: str = Field(..., description="The validated SQL query to run")


# Create tools list
tools = [
    pydantic_function_tool(ListTablesArgs),
    pydantic_function_tool(DescribeTableArgs),
    pydantic_function_tool(SampleTableArgs),
    pydantic_function_tool(RunTestSQLQuery),
    pydantic_function_tool(RunFinalSQLQuery),
]

AGENT_PROMPT = """<purpose>
    You are a world-class expert at crafting precise DuckDB SQL queries.
    Your goal is to generate accurate queries that exactly match the user's data needs.
</purpose>

<instructions>
    <instruction>Use the provided tools to explore the database and construct the perfect query.</instruction>
    <instruction>Start by listing tables to understand what's available.</instruction>
    <instruction>Describe tables to understand their schema and columns.</instruction>
    <instruction>Sample tables to see actual data patterns.</instruction>
    <instruction>Test queries before finalizing them.</instruction>
    <instruction>Only call run_final_sql_query when you're confident the query is perfect.</instruction>
    <instruction>Be thorough but efficient with tool usage.</instruction>
    <instruction>If you find your run_test_sql_query tool call returns an error or won't satisfy the user request, try to fix the query or try a different query.</instruction>
    <instruction>Think step by step about what information you need.</instruction>
    <instruction>Be sure to specify every parameter for each tool call.</instruction>
    <instruction>Every tool call should have a reasoning parameter which gives you a place to explain why you are calling the tool.</instruction>
</instructions>

<tools>
    <tool>
        <name>list_tables</name>
        <description>Returns list of available tables in database</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Why we need to list tables relative to user request</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>describe_table</name>
        <description>Returns schema info for specified table</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Why we need to describe this table</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>table_name</name>
                <type>string</type>
                <description>Name of table to describe</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>sample_table</name>
        <description>Returns sample rows from specified table, always specify row_sample_size</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Why we need to sample this table</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>table_name</name>
                <type>string</type>
                <description>Name of table to sample</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>row_sample_size</name>
                <type>integer</type>
                <description>Number of rows to sample aim for 3-5 rows</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>run_test_sql_query</name>
        <description>Tests a SQL query and returns results (only visible to agent)</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Why we're testing this specific query</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>sql_query</name>
                <type>string</type>
                <description>The SQL query to test</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>run_final_sql_query</name>
        <description>Runs the final validated SQL query and shows results to user</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Final explanation of how query satisfies user request</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>sql_query</name>
                <type>string</type>
                <description>The validated SQL query to run</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
</tools>

<user-request>
    {{user_request}}
</user-request>
"""


def list_tables(reasoning: str) -> List[str]:
    try:
        result = subprocess.run(
            f'duckdb {DB_PATH} -c ".tables"',
            shell=True,
            text=True,
            capture_output=True,
        )
        console.log(f"[blue]List Tables Tool[/blue] - Reasoning: {reasoning}")
        return result.stdout.strip().split("\n")
    except Exception as e:
        console.log(f"[red]Error listing tables: {str(e)}[/red]")
        return []


def describe_table(reasoning: str, table_name: str) -> str:
    try:
        result = subprocess.run(
            f'duckdb {DB_PATH} -c "DESCRIBE {table_name};"',
            shell=True,
            text=True,
            capture_output=True,
        )
        console.log(
            f"[blue]Describe Table Tool[/blue] - Table: {table_name} - Reasoning: {reasoning}"
        )
        return result.stdout
    except Exception as e:
        console.log(f"[red]Error describing table: {str(e)}[/red]")
        return ""


def sample_table(reasoning: str, table_name: str, row_sample_size: int) -> str:
    try:
        result = subprocess.run(
            f'duckdb {DB_PATH} -c "SELECT * FROM {table_name} LIMIT {row_sample_size};"',
            shell=True,
            text=True,
            capture_output=True,
        )
        console.log(
            f"[blue]Sample Table Tool[/blue] - Table: {table_name} - Rows: {row_sample_size} - Reasoning: {reasoning}"
        )
        return result.stdout
    except Exception as e:
        console.log(f"[red]Error sampling table: {str(e)}[/red]")
        return ""


def run_test_sql_query(reasoning: str, sql_query: str) -> str:
    try:
        result = subprocess.run(
            f'duckdb {DB_PATH} -c "{sql_query}"',
            shell=True,
            text=True,
            capture_output=True,
        )
        console.log(f"[blue]Test Query Tool[/blue] - Reasoning: {reasoning}")
        console.log(f"[dim]Query: {sql_query}[/dim]")
        return result.stdout
    except Exception as e:
        console.log(f"[red]Error running test query: {str(e)}[/red]")
        return str(e)


def run_final_sql_query(reasoning: str, sql_query: str) -> str:
    try:
        result = subprocess.run(
            f'duckdb {DB_PATH} -c "{sql_query}"',
            shell=True,
            text=True,
            capture_output=True,
        )
        console.log(
            Panel(
                f"[green]Final Query Tool[/green]\nReasoning: {reasoning}\nQuery: {sql_query}"
            )
        )
        return result.stdout
    except Exception as e:
        console.log(f"[red]Error running final query: {str(e)}[/red]")
        return str(e)


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="DuckDB Agent using OpenRouter API")
    parser.add_argument(
        "-d", "--db", required=True, help="Path to DuckDB database file"
    )
    parser.add_argument("-p", "--prompt", required=True, help="The user's request")
    parser.add_argument(
        "-c",
        "--compute",
        type=int,
        default=10,
        help="Maximum number of agent loops (default: 10)",
    )
    args = parser.parse_args()

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        console.print(
            "[red]Error: OPENROUTER_API_KEY environment variable is not set[/red]"
        )
        sys.exit(1)
    openrouter.api_key = OPENROUTER_API_KEY

    global DB_PATH
    DB_PATH = args.db

    completed_prompt = AGENT_PROMPT.replace("{{user_request}}", args.prompt)
    messages = [{"role": "user", "content": completed_prompt}]

    compute_iterations = 0
    while True:
        console.rule(
            f"[yellow]Agent Loop {compute_iterations + 1}/{args.compute}[/yellow]"
        )
        compute_iterations += 1

        if compute_iterations >= args.compute:
            console.print(
                "[yellow]Warning: Reached maximum compute loops without final query[/yellow]"
            )
            raise Exception(
                f"Maximum compute loops reached: {compute_iterations}/{args.compute}"
            )

        try:
            response = openrouter.Completion.create(
                model="o3-mini",
                messages=messages,
                tools=tools,
                tool_choice="required",
                headers={"X-OpenRouter-Source": "DuckDBAgent"}
            )

            if response.choices:
                assert len(response.choices) == 1
                message = response.choices[0].message

                if message.function_call:
                    func_call = message.function_call
                elif message.tool_calls and len(message.tool_calls) > 0:
                    tool_call = message.tool_calls[0]
                    func_call = tool_call.function
                else:
                    func_call = None

                if func_call:
                    func_name = func_call.name
                    func_args_str = func_call.arguments

                    messages.append(
                        {
                            "role": "assistant",
                            "tool_calls": [
                                {
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": func_call,
                                }
                            ],
                        }
                    )

                    console.print(
                        f"[blue]Function Call:[/blue] {func_name}({func_args_str})"
                    )
                    try:
                        if func_name == "ListTablesArgs":
                            args_parsed = ListTablesArgs.model_validate_json(
                                func_args_str
                            )
                            result = list_tables(reasoning=args_parsed.reasoning)
                        elif func_name == "DescribeTableArgs":
                            args_parsed = DescribeTableArgs.model_validate_json(
                                func_args_str
                            )
                            result = describe_table(
                                reasoning=args_parsed.reasoning,
                                table_name=args_parsed.table_name,
                            )
                        elif func_name == "SampleTableArgs":
                            args_parsed = SampleTableArgs.model_validate_json(
                                func_args_str
                            )
                            result = sample_table(
                                reasoning=args_parsed.reasoning,
                                table_name=args_parsed.table_name,
                                row_sample_size=args_parsed.row_sample_size,
                            )
                        elif func_name == "RunTestSQLQuery":
                            args_parsed = RunTestSQLQuery.model_validate_json(
                                func_args_str
                            )
                            result = run_test_sql_query(
                                reasoning=args_parsed.reasoning,
                                sql_query=args_parsed.sql_query,
                            )
                        elif func_name == "RunFinalSQLQuery":
                            args_parsed = RunFinalSQLQuery.model_validate_json(
                                func_args_str
                            )
                            result = run_final_sql_query(
                                reasoning=args_parsed.reasoning,
                                sql_query=args_parsed.sql_query,
                            )
                            console.print("\n[green]Final Results:[/green]")
                            console.print(result)
                            return
                        else:
                            raise Exception(f"Unknown tool call: {func_name}")

                        console.print(
                            f"[blue]Function Call Result:[/blue] {func_name}(...) ->\n{result}"
                        )

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps({"result": str(result)}),
                            }
                        )

                    except Exception as e:
                        error_msg = f"Argument validation failed for {func_name}: {e}"
                        console.print(f"[red]{error_msg}[/red]")
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps({"error": error_msg}),
                            }
                        )
                        continue
                else:
                    raise Exception(
                        "No function call in this response - should never happen"
                    )
        except Exception as e:
            console.print(f"[red]Error in agent loop: {str(e)}[/red]")
            raise e


if __name__ == "__main__":
    main()
