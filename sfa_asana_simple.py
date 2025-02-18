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

To set this up you need a Personal Access Token (PAT) for Asana:
https://app.asana.com/0/my-account/security/tokens-and-oauth

Set the environment variable ANTHROPIC_API_KEY with your Anthropic API key:
export ANTHROPIC_API_KEY="your-api-key"

Also, set the environment variable ASANA_ACCESS_TOKEN with your Asana PAT:
export ASANA_ACCESS_TOKEN="your-asana-access-token"

Replace the project id with your own project id:

# List tasks in a project:
uv run sfa_asana_anthropic.py --project "1234567890" -p "List all tasks in the project"

# Get detailed raw data for a specific task:
uv run sfa_asana_anthropic.py --project "1234567890" -p "Show me the full details for task <task_id>"
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import List

import asana
from anthropic import Anthropic
from rich.console import Console
from rich.panel import Panel


# ---------------------------
# Asana Utilities
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
            """Return a human-readable summary including key details, custom fields, and comments."""
            task = data.get(
                "data", data
            )  # In case the API wraps the task in {"data": ...}
            output = []
            output.append(f"Task: {task.get('name', 'Unnamed')}")
            output.append(f"ID: {task.get('gid', 'No ID')}")
            output.append(f"Resource Type: {task.get('resource_type', '')}")
            output.append(f"Subtype: {task.get('resource_subtype', '')}")
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

            # Custom Fields
            custom_fields = task.get("custom_fields", [])
            if custom_fields:
                output.append("\nCustom Fields:")
                for cf in custom_fields:
                    name = cf.get("name")
                    value = (
                        cf.get("display_value")
                        or cf.get("text_value")
                        or cf.get("number_value")
                    )
                    output.append(f" - {name}: {value}")

            # Memberships
            memberships = task.get("memberships", [])
            if memberships:
                output.append("\nMemberships:")
                for m in memberships:
                    proj = m.get("project", {}).get("name", "Unknown Project")
                    sect = m.get("section", {}).get("name", "Unknown Section")
                    output.append(f" - Project: {proj} | Section: {sect}")

            # Dependencies (if any)
            dependencies = task.get("dependencies", [])
            if dependencies:
                output.append("\nDependencies:")
                for dep in dependencies:
                    output.append(f" - {dep.get('gid')}")

            # Comments (Stories)
            stories = task.get("stories", [])
            if stories:
                output.append("\nComments:")
                for story in stories:
                    if story.get("type") == "comment":
                        creator = story.get("created_by", {}).get("name", "Unknown")
                        text = story.get("text", "")
                        created = AsanaUtils.Formatters.format_date(
                            story.get("created_at")
                        )
                        output.append(f" - [{created}] {creator}: {text}")

            url = task.get("permalink_url")
            if url:
                output.append(f"\nURL: {url}")

            return "\n".join(output)


# ---------------------------
# End Asana Utilities
# ---------------------------

# Initialize rich console
console = Console()

# Global variables for Asana project and client (set in main)
ASANA_PROJECT_ID = None
asana_client = None

# -----------------------------------------------------------------------------
# Tool Functions
# -----------------------------------------------------------------------------


def list_tasks(reasoning: str) -> List[str]:
    """
    Returns a concise list of tasks (IDs and names) for the specified Asana project.
    This gives the agent a quick overview without overwhelming context.
    """
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


def get_task_raw(reasoning: str, task_id: str) -> str:
    """
    Returns the full raw JSON data for a specific task identified by its ID.
    This includes a comprehensive set of fields and comments (stories).
    """
    try:
        # A comprehensive set of fields for full details:
        opt_fields = (
            "gid,name,resource_type,resource_subtype,created_by,approval_status,assignee_status,"
            "completed,completed_at,completed_by,created_at,dependencies,dependents,due_at,due_on,"
            "external,html_notes,hearted,hearts,hearts.user,liked,likes,likes.user,"
            "memberships,memberships.project,memberships.project.name,memberships.section,memberships.section.name,"
            "modified_at,notes,num_hearts,num_likes,num_subtasks,start_at,start_on,actual_time_minutes,"
            "assignee,assignee.name,assignee_section,assignee_section.name,custom_fields,custom_fields.gid,"
            "custom_fields.resource_type,custom_fields.name,custom_fields.type,custom_fields.enum_options,"
            "custom_fields.enum_options.gid,custom_fields.enum_options.name,custom_fields.enum_options.enabled,"
            "custom_fields.enum_options.color,custom_fields.enabled,custom_fields.representation_type,"
            "custom_fields.id_prefix,custom_fields.is_formula_field,custom_fields.is_global_to_workspace,"
            "custom_fields.is_value_read_only,custom_fields.multi_enum_values,custom_fields.multi_enum_values.gid,"
            "custom_fields.multi_enum_values.name,custom_fields.multi_enum_values.enabled,custom_fields.multi_enum_values.color,"
            "custom_fields.number_value,custom_fields.text_value,custom_fields.display_value,custom_fields.description,"
            "custom_fields.precision,custom_fields.format,custom_fields.currency_code,custom_fields.custom_label,"
            "custom_fields.custom_label_position,custom_fields.created_by,custom_fields.created_by.name,"
            "custom_fields.people_value,custom_fields.people_value.name,custom_fields.privacy_setting,"
            "custom_fields.default_access_level,custom_fields.resource_subtype,custom_fields.custom_type,"
            "custom_fields.custom_type_status_option,followers,followers.name,parent,parent.created_by,parent.name,"
            "parent.resource_subtype,projects,projects.name,tags,tags.name,workspace,workspace.name,permalink_url"
        )
        # Request the task with the full set of fields
        task = asana_client.tasks_api.get_task(
            task_id, opts={"opt_fields": opt_fields, "opt_pretty": True}
        )
        task_dict = task.to_dict() if hasattr(task, "to_dict") else task

        # Retrieve comments (stories) for the task
        stories = asana_client.stories_api.get_stories_for_task(
            task_id,
            opts={
                "opt_fields": "gid,type,text,created_at,created_by,created_by.name",
                "opt_pretty": True,
            },
        )
        stories_list = list(stories)
        task_dict["stories"] = stories_list

        console.log(
            f"[blue]Get Task Raw Tool[/blue] - Task ID: {task_id} - Reasoning: {reasoning}"
        )
        return json.dumps(task_dict, indent=2)
    except Exception as e:
        console.log(f"[red]Error getting raw data for task {task_id}: {str(e)}[/red]")
        return str(e)


def describe_task(reasoning: str, task_id: str) -> str:
    """
    Returns a human-readable summary for a specific task.
    It uses the full raw data to provide a detailed summary including custom fields and comments.
    """
    try:
        raw_json = get_task_raw(reasoning, task_id)
        # Parse the JSON to a dict
        task_data = json.loads(raw_json)
        formatted = AsanaUtils.Formatters.format_task_data(task_data)
        console.log(
            f"[blue]Describe Task Tool[/blue] - Task: {task_id} - Reasoning: {reasoning}"
        )
        return formatted
    except Exception as e:
        console.log(f"[red]Error describing task {task_id}: {str(e)}[/red]")
        return str(e)


# -----------------------------------------------------------------------------
# Agent Prompt for Asana
# -----------------------------------------------------------------------------

AGENT_PROMPT = """<purpose>
    You are a world-class expert at extracting and understanding data from Asana projects.
    Your goal is to obtain any specific data required about the project by using the provided tools.
    You can first list all tasks (IDs and names) and then fetch detailed raw data for specific tasks.
</purpose>

<instructions>
    <instruction>Use the provided tools to explore the Asana project and extract any data needed.</instruction>
    <instruction>Begin by calling list_tasks to get an overview of the project’s tasks.</instruction>
    <instruction>When you need more details, call get_task_raw or describe_task with the specific task ID.</instruction>
    <instruction>If the user request refers to multiple tasks, you may call the detailed tool in a loop.</instruction>
    <instruction>Include a reasoning parameter in every tool call to explain your purpose.</instruction>
</instructions>

<tools>
    <tool>
        <name>list_tasks</name>
        <description>Returns a concise list of tasks (IDs and names) in the Asana project.</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Explain why you need to list the tasks.</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>get_task_raw</name>
        <description>Returns the complete raw JSON data for a specific task, including custom fields, memberships, dependencies, and comments.</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Explain why you need the raw data for this task.</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>task_id</name>
                <type>string</type>
                <description>The ID of the task to retrieve raw data for.</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>describe_task</name>
        <description>Returns a detailed, human-readable summary for a specific task, including custom fields and comments.</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Explain why you need to describe this task.</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>task_id</name>
                <type>string</type>
                <description>The ID of the task to describe.</description>
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
                        "description": "Returns a concise list of tasks (IDs and names) in the Asana project",
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
                        "name": "get_task_raw",
                        "description": "Returns the complete raw JSON data for a specific task",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "reasoning": {
                                    "type": "string",
                                    "description": "Explanation for retrieving raw task data",
                                },
                                "task_id": {
                                    "type": "string",
                                    "description": "The ID of the task to retrieve",
                                },
                            },
                            "required": ["reasoning", "task_id"],
                        },
                    },
                    {
                        "name": "describe_task",
                        "description": "Returns a detailed, human-readable summary for a specific task",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "reasoning": {
                                    "type": "string",
                                    "description": "Explanation for describing this task",
                                },
                                "task_id": {
                                    "type": "string",
                                    "description": "The ID of the task to describe",
                                },
                            },
                            "required": ["reasoning", "task_id"],
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
                        elif func_name == "get_task_raw":
                            result = get_task_raw(
                                reasoning=func_args["reasoning"],
                                task_id=func_args["task_id"],
                            )
                        elif func_name == "describe_task":
                            result = describe_task(
                                reasoning=func_args["reasoning"],
                                task_id=func_args["task_id"],
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
