#!/usr/bin/env python3

# /// script
# dependencies = [
#   "anthropic>=0.45.2",
#   "rich>=13.7.0",
#   "asana",
# ]
# ///


"""
Example Usage:

To set this up you need a PAT (Personal Access Token) for Asana:
https://app.asana.com/0/my-account/security/tokens-and-oauth

Set the environment variable ANTHROPIC_API_KEY with your API key:
export ANTHROPIC_API_KEY="your-api-key"

replace the project id with your own project id

# List tasks in a project:
uv run sfa_asana_anthropic.py --project "1234567890" -p "List all tasks in the project"

# Query tasks by substring:
uv run sfa_asana_anthropic.py --project "1234567890" -p "Show me tasks that mention 'urgent'" -c 5
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import List

# Import your Asana utilities (this could be an import from a module)
# from asana_utils import AsanaUtils
import asana
from anthropic import Anthropic
from rich.console import Console
from rich.panel import Panel


# ---------------------------
# Example Asana Utilities
# ---------------------------
class AsanaUtils:
    class Client:
        from dataclasses import dataclass

        @dataclass
        class AsanaClient:
            client: asana.ApiClient = None
            tasks_api: asana.TasksApi = None
            stories_api: asana.StoriesApi = None
            attachments_api: asana.AttachmentsApi = None

            def __post_init__(self):
                access_token = os.getenv("ASANA_ACCESS_TOKEN")
                if not access_token:
                    raise ValueError("ASANA_ACCESS_TOKEN environment variable not set")
                configuration = asana.Configuration()
                configuration.access_token = access_token
                if self.client is None:
                    self.client = asana.ApiClient(configuration)
                if self.tasks_api is None:
                    self.tasks_api = asana.TasksApi(self.client)
                if self.stories_api is None:
                    self.stories_api = asana.StoriesApi(self.client)
                if self.attachments_api is None:
                    self.attachments_api = asana.AttachmentsApi(self.client)

    class Formatters:
        @staticmethod
        def format_date(date_str: str | None) -> str:
            if not date_str:
                return ""
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                return date_str

        @staticmethod
        def format_task_data(data: dict) -> str:
            if "error" in data:
                return f"Error: {data['error']}"
            task = data.get("task", data)
            stories = data.get("stories", [])
            attachments = data.get("attachments", [])
            output = []
            output.append(f"Task: {task.get('name', 'Unnamed')}")
            output.append(f"ID: {task.get('gid', 'No ID')}")
            output.append(
                f"Status: {'Completed' if task.get('completed') else 'Active'}"
            )
            if task.get("created_at"):
                output.append(
                    f"Created: {AsanaUtils.Formatters.format_date(task['created_at'])}"
                )
            if task.get("modified_at"):
                output.append(
                    f"Modified: {AsanaUtils.Formatters.format_date(task['modified_at'])}"
                )
            assignee = task.get("assignee", {})
            if assignee:
                output.append(f"Assignee: {assignee.get('name', 'Unknown')}")
            notes = task.get("notes")
            if notes:
                output.append(f"\nNotes:\n{notes}")
            # (Additional formatting for memberships, custom fields, comments, etc.)
            url = task.get("permalink_url")
            if url:
                output.append(f"\nURL: {url}")
            return "\n".join(output)

    class TaskOperations:
        @staticmethod
        def get_task_details(
            tasks_api, stories_api, attachments_api, users_api, task_id: str
        ) -> dict:
            try:
                # Get task details (using a simple opt_fields string for demonstration)
                opt_fields = "gid,name,notes,completed,created_at,modified_at,assignee,permalink_url"
                task = tasks_api.get_task(task_id, opts={"opt_fields": opt_fields})
                task_dict = task if isinstance(task, dict) else task.to_dict()
                # Get stories (comments) and attachments if desired…
                return task_dict
            except Exception as e:
                return {"error": str(e)}


# ---------------------------
# End Asana Utilities
# ---------------------------

# Initialize rich console
console = Console()

# Global variables for Asana project and client (set in main)
ASANA_PROJECT_ID = None
asana_client = None

# -----------------------------------------------------------------------------
# Tool Functions (mirroring the DuckDB agent but for Asana)
# -----------------------------------------------------------------------------


def list_tasks(reasoning: str) -> List[str]:
    """Returns a list of tasks (id and name) for the specified Asana project."""
    try:
        tasks = asana_client.tasks_api.get_tasks_for_project(
            ASANA_PROJECT_ID, opts={"fields": "gid,name"}
        )
        tasks_list = list(tasks)
        console.log(f"[blue]List Tasks Tool[/blue] - Reasoning: {reasoning}")
        return [f"{task['gid']}: {task['name']}" for task in tasks_list]
    except Exception as e:
        console.log(f"[red]Error listing tasks: {str(e)}[/red]")
        return []


def describe_task(reasoning: str, task_id: str) -> str:
    """Returns detailed information for a specified task."""
    try:
        details = AsanaUtils.TaskOperations.get_task_details(
            asana_client.tasks_api,
            asana_client.stories_api,
            asana_client.attachments_api,
            None,
            task_id,
        )
        console.log(
            f"[blue]Describe Task Tool[/blue] - Task: {task_id} - Reasoning: {reasoning}"
        )
        return AsanaUtils.Formatters.format_task_data(details)
    except Exception as e:
        console.log(f"[red]Error describing task: {str(e)}[/red]")
        return ""


def sample_tasks(reasoning: str, row_sample_size: int) -> str:
    """Returns a sample (first N) of tasks from the Asana project."""
    try:
        tasks = asana_client.tasks_api.get_tasks_for_project(
            ASANA_PROJECT_ID, opts={"fields": "gid,name"}
        )
        tasks_list = list(tasks)
        sample = tasks_list[:row_sample_size]
        console.log(
            f"[blue]Sample Tasks Tool[/blue] - Rows: {row_sample_size} - Reasoning: {reasoning}"
        )
        return "\n".join([f"{task['gid']}: {task['name']}" for task in sample])
    except Exception as e:
        console.log(f"[red]Error sampling tasks: {str(e)}[/red]")
        return ""


def run_test_task_query(reasoning: str, query: str) -> str:
    """
    Tests a task query by returning tasks whose names contain the query substring.
    (This is only visible to the agent.)
    """
    try:
        tasks = asana_client.tasks_api.get_tasks_for_project(
            ASANA_PROJECT_ID, opts={"fields": "gid,name"}
        )
        tasks_list = list(tasks)
        filtered = [
            task for task in tasks_list if query.lower() in task["name"].lower()
        ]
        console.log(f"[blue]Test Task Query Tool[/blue] - Reasoning: {reasoning}")
        return "\n".join([f"{task['gid']}: {task['name']}" for task in filtered])
    except Exception as e:
        console.log(f"[red]Error running test task query: {str(e)}[/red]")
        return str(e)


def run_final_task_query(reasoning: str, query: str) -> str:
    """
    Runs the final validated task query and returns detailed results to the user.
    """
    try:
        tasks = asana_client.tasks_api.get_tasks_for_project(
            ASANA_PROJECT_ID, opts={"fields": "gid,name"}
        )
        tasks_list = list(tasks)
        filtered = [
            task for task in tasks_list if query.lower() in task["name"].lower()
        ]
        results = []
        for task in filtered:
            details = AsanaUtils.TaskOperations.get_task_details(
                asana_client.tasks_api,
                asana_client.stories_api,
                asana_client.attachments_api,
                None,
                task["gid"],
            )
            results.append(AsanaUtils.Formatters.format_task_data(details))
        console.log(f"[blue]Final Task Query Tool[/blue] - Reasoning: {reasoning}")
        return "\n\n".join(results)
    except Exception as e:
        console.log(f"[red]Error running final task query: {str(e)}[/red]")
        return str(e)


# -----------------------------------------------------------------------------
# Agent Prompt for Asana
# -----------------------------------------------------------------------------

AGENT_PROMPT = """<purpose>
    You are a world-class expert at understanding Asana projects and crafting precise responses to retrieve relevant project information.
    Your goal is to generate accurate responses that exactly match the user's data needs regarding the Asana project.
</purpose>

<instructions>
    <instruction>Use the provided tools to explore the Asana project and construct the perfect response.</instruction>
    <instruction>Start by listing tasks to understand what’s available.</instruction>
    <instruction>Describe tasks to get detailed information.</instruction>
    <instruction>Sample tasks to see actual data patterns.</instruction>
    <instruction>Test queries before finalizing them.</instruction>
    <instruction>Only call run_final_task_query when you’re confident the query is perfect.</instruction>
    <instruction>Be thorough but efficient with tool usage.</instruction>
    <instruction>If you find your run_test_task_query tool call returns an error or won’t satisfy the user request, refine the query.</instruction>
    <instruction>Think step by step about what information you need.</instruction>
    <instruction>Be sure to specify every parameter for each tool call.</instruction>
    <instruction>Every tool call should have a reasoning parameter which explains why you are calling the tool.</instruction>
</instructions>

<tools>
    <tool>
        <name>list_tasks</name>
        <description>Returns list of tasks in the Asana project</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Why we need to list tasks relative to the user request</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>describe_task</name>
        <description>Returns detailed information for a specified task</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Why we need to describe this task</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>task_id</name>
                <type>string</type>
                <description>ID of task to describe</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>sample_tasks</name>
        <description>Returns a sample of tasks from the Asana project</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Why we need to sample tasks</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>row_sample_size</name>
                <type>integer</type>
                <description>Number of tasks to sample (aim for 3-5 tasks)</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>run_test_task_query</name>
        <description>Tests a task query and returns results (only visible to agent)</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Why we’re testing this specific query</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>query</name>
                <type>string</type>
                <description>The task query to test (as a substring match)</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>run_final_task_query</name>
        <description>Runs the final validated task query and shows results to the user</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Final explanation of how the query satisfies the user request</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>query</name>
                <type>string</type>
                <description>The validated task query to run (as a substring match)</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
</tools>

<user-request>
    {{user_request}}
</user-request>
"""

# -----------------------------------------------------------------------------
# Main Agent Loop
# -----------------------------------------------------------------------------


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Asana Project Agent using Anthropic API"
    )
    parser.add_argument("-p", "--prompt", required=True, help="The user's request")
    parser.add_argument("-pr", "--project", required=True, help="Asana project ID")
    parser.add_argument(
        "-c", "--compute", type=int, default=10, help="Maximum number of agent loops"
    )
    args = parser.parse_args()

    # Set global Asana project id and initialize Asana client
    global ASANA_PROJECT_ID, asana_client
    ASANA_PROJECT_ID = args.project

    try:
        asana_client = AsanaUtils.Client.AsanaClient(
            client=None, tasks_api=None, stories_api=None, attachments_api=None
        )
    except Exception as e:
        console.print(f"[red]Error initializing Asana client: {str(e)}[/red]")
        sys.exit(1)

    # Check for Anthropic API key
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if not ANTHROPIC_API_KEY:
        console.print(
            "[red]Error: ANTHROPIC_API_KEY environment variable is not set[/red]"
        )
        sys.exit(1)

    client = Anthropic()

    # Create the combined prompt
    completed_prompt = AGENT_PROMPT.replace("{{user_request}}", args.prompt)
    messages = [{"role": "user", "content": completed_prompt}]
    compute_iterations = 0

    # Main agent loop
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
            if compute_iterations == 1:
                messages.append({"role": "user", "content": args.prompt})

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=messages,
                tools=[
                    {
                        "name": "list_tasks",
                        "description": "Returns list of tasks in the Asana project",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "reasoning": {
                                    "type": "string",
                                    "description": "Explanation for listing tasks",
                                }
                            },
                            "required": ["reasoning"],
                        },
                    },
                    {
                        "name": "describe_task",
                        "description": "Returns detailed information for a specified task",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "reasoning": {
                                    "type": "string",
                                    "description": "Why we need to describe this task",
                                },
                                "task_id": {
                                    "type": "string",
                                    "description": "ID of task to describe",
                                },
                            },
                            "required": ["reasoning", "task_id"],
                        },
                    },
                    {
                        "name": "sample_tasks",
                        "description": "Returns a sample of tasks from the Asana project",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "reasoning": {
                                    "type": "string",
                                    "description": "Why we need to sample tasks",
                                },
                                "row_sample_size": {
                                    "type": "integer",
                                    "description": "Number of tasks to sample (aim for 3-5 tasks)",
                                },
                            },
                            "required": ["reasoning", "row_sample_size"],
                        },
                    },
                    {
                        "name": "run_test_task_query",
                        "description": "Tests a task query and returns results (only visible to agent)",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "reasoning": {
                                    "type": "string",
                                    "description": "Why we're testing this specific query",
                                },
                                "query": {
                                    "type": "string",
                                    "description": "The task query to test (as a substring match)",
                                },
                            },
                            "required": ["reasoning", "query"],
                        },
                    },
                    {
                        "name": "run_final_task_query",
                        "description": "Runs the final validated task query and shows results to the user",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "reasoning": {
                                    "type": "string",
                                    "description": "Final explanation of how the query satisfies the user request",
                                },
                                "query": {
                                    "type": "string",
                                    "description": "The validated task query to run (as a substring match)",
                                },
                            },
                            "required": ["reasoning", "query"],
                        },
                    },
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
                    messages.append({"role": "assistant", "content": response.content})

                    try:
                        if func_name == "list_tasks":
                            result = list_tasks(reasoning=func_args["reasoning"])
                        elif func_name == "describe_task":
                            result = describe_task(
                                reasoning=func_args["reasoning"],
                                task_id=func_args["task_id"],
                            )
                        elif func_name == "sample_tasks":
                            result = sample_tasks(
                                reasoning=func_args["reasoning"],
                                row_sample_size=func_args["row_sample_size"],
                            )
                        elif func_name == "run_test_task_query":
                            result = run_test_task_query(
                                reasoning=func_args["reasoning"],
                                query=func_args["query"],
                            )
                        elif func_name == "run_final_task_query":
                            result = run_final_task_query(
                                reasoning=func_args["reasoning"],
                                query=func_args["query"],
                            )
                            console.print("\n[green]Final Results:[/green]")
                            console.print(result)
                            return
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
                raise Exception("No tool calls found in response - should never happen")

        except Exception as e:
            console.print(f"[red]Error in agent loop: {str(e)}[/red]")
            raise e


if __name__ == "__main__":
    main()
