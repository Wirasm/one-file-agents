# One-File Agents

This project provides single-file agents that run using UV.

## Prerequisites
- Install UV (download it from the official site).
- Set the necessary environment variables.

## Usage
Run the following command as an example:

```bash
uv run sfa_duckdb_openai.py -d analytics.db -p "list the number of tables in the db" -c 5
```

## Agent Loop Explanation

The agent loop is the core processing cycle within the project and functions as follows:

- **Initialization:** The main function sets up the environment by parsing command-line arguments (including the database path, user prompt, and maximum compute iterations) and configuring the API key.

- **Prompt Construction:** The user prompt is merged into a comprehensive agent prompt that outlines the operational instructions and available tools.

- **Iterative Processing:** Within a while-loop, the agent sends the current conversation (messages) to the OpenAI API, which generates responses that may include tool calls.

- **Tool Integration:** If a function call is detected in the response, the corresponding tool (e.g., listing tables, describing a table, sampling data, or running a query) is executed. The result of the function call is logged, appended to the conversation messages, and used to refine subsequent requests.

- **Termination:** The loop continues until a final validated SQL query is successfully executed or the maximum number of iterations is reached, in which case a warning is raised.

This structured loop ensures that the agent incrementally refines its query, integrating feedback from each step to achieve a robust final result.

## Single File Agents Concept

This concept is made possible by UV.
The project is built around the idea of single file agents, which consolidate all necessary components in one file. This approach offers several benefits:

- **Simplicity:** All configuration, tool definitions, and the main agent loop are contained in a single file, making it easier to understand and manage.
- **Modularity:** Despite being a single file, the structure is modular. Each tool is well-defined and documented, promoting reusable code.
- **Rapid Prototyping:** Developers can quickly iterate on the agent logic without navigating through multiple files.

This design pattern is particularly useful for building lightweight, yet powerful, agents that are easy to deploy and maintain.
