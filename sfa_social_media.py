#!/usr/bin/env python3

# /// script
# dependencies = [
#   "anthropic>=0.45.2",
#   "rich>=13.7.0",
# ]
# ///

"""
Enhanced Social Media Agent that generates and refines posts from ideas.

Example Usage:
export ANTHROPIC_API_KEY="your-api-key"

Run the agent with:
uv run sfa_social_media.py --idea "Share excitement about AI progress in 2024" --tone "professional but engaging" --target "tech professionals" -c 100
"""

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple

from anthropic import Anthropic
from rich.console import Console
from rich.panel import Panel

# Initialize rich console
console = Console()

# -----------------------------------------------------------------------------
# Data Structures
# -----------------------------------------------------------------------------


@dataclass
class PostMetrics:
    word_count: int
    hashtag_count: int
    engagement_triggers: int
    technical_terms: int
    sentiment_score: float

    def is_optimal(self) -> bool:
        return (
            15 <= self.word_count <= 50
            and self.hashtag_count >= 2
            and self.engagement_triggers >= 1
            and self.technical_terms >= 2
            and 0.5 <= self.sentiment_score <= 1.0
        )


class PostContent:
    def __init__(self, content: str, metrics: PostMetrics = None):
        self.content = content
        self.metrics = metrics

    def __eq__(self, other) -> bool:
        if not isinstance(other, PostContent):
            return False
        return self.content.strip() == other.content.strip()

    def __str__(self) -> str:
        return self.content


# -----------------------------------------------------------------------------
# Post Generation and Analysis Utilities
# -----------------------------------------------------------------------------


class ContentGenerator:
    """Handles post generation with various templates and styles."""

    # Technical terms that indicate domain expertise
    TECH_TERMS = {
        "ai": [
            "artificial intelligence",
            "machine learning",
            "neural networks",
            "deep learning",
        ],
        "tools": ["algorithms", "models", "frameworks", "architectures"],
        "metrics": ["accuracy", "efficiency", "performance", "scalability"],
        "applications": ["computer vision", "nlp", "robotics", "automation"],
    }

    # Template components for post generation
    TEMPLATES = {
        "professional but engaging": {
            "tech professionals": {
                "openings": [
                    "🚀 Breaking AI Milestone:",
                    "💡 Tech Innovation Alert:",
                    "🔬 AI Research Breakthrough:",
                ],
                "bodies": [
                    "The latest advances in {tech} are showing {metric} improvements in {application}.",
                    "Groundbreaking developments in {tech} have achieved unprecedented {metric} in {application}.",
                    "New {tech} architectures are revolutionizing {application} with exceptional {metric}.",
                ],
                "closings": [
                    "What's your take on this advancement? #AI #Tech",
                    "How are you leveraging these capabilities? #AIProgress #Innovation",
                    "Share your experiences with similar implementations! #TechTrends #AI",
                ],
            }
        }
    }

    @classmethod
    def generate(cls, idea: str, tone: str, target: str) -> str:
        """Generates a post using appropriate templates and style."""
        if tone not in cls.TEMPLATES or target not in cls.TEMPLATES[tone]:
            raise ValueError(f"Unsupported tone '{tone}' or target '{target}'")

        templates = cls.TEMPLATES[tone][target]

        # Select components
        opening = random.choice(templates["openings"])
        body = random.choice(templates["bodies"])
        closing = random.choice(templates["closings"])

        # Fill in template variables
        tech = random.choice(cls.TECH_TERMS["ai"])
        metric = random.choice(cls.TECH_TERMS["metrics"])
        application = random.choice(cls.TECH_TERMS["applications"])

        body = body.format(tech=tech, metric=metric, application=application)

        # Combine components
        post = f"{opening} {body} {closing}"
        return post


class ContentAnalyzer:
    """Analyzes post content for various metrics and quality indicators."""

    @staticmethod
    def analyze(post: str) -> PostMetrics:
        """Analyzes a post and returns metrics."""
        words = post.split()

        # Calculate basic metrics
        metrics = PostMetrics(
            word_count=len(words),
            hashtag_count=sum(1 for word in words if word.startswith("#")),
            engagement_triggers=sum(1 for word in words if "?" in word),
            technical_terms=sum(
                1
                for word in words
                if word.lower()
                in [
                    term
                    for terms in ContentGenerator.TECH_TERMS.values()
                    for term in terms
                ]
            ),
            sentiment_score=ContentAnalyzer._calculate_sentiment(post),
        )

        return metrics

    @staticmethod
    def _calculate_sentiment(text: str) -> float:
        """Calculates a basic sentiment score (0-1) based on presence of positive indicators."""
        positive_indicators = {
            "breakthrough",
            "innovation",
            "advanced",
            "impressive",
            "revolutionary",
            "exciting",
            "groundbreaking",
            "🚀",
            "💡",
            "🔬",
        }
        words = set(text.lower().split())
        score = sum(1 for word in words if word in positive_indicators) / max(
            len(words), 1
        )
        return min(score + 0.5, 1.0)  # Base score of 0.5 plus indicators


class ContentRefiner:
    """Handles post refinement based on analysis metrics."""

    @staticmethod
    def refine(post: str, metrics: PostMetrics) -> str:
        """Refines a post based on its metrics."""
        refined = post

        # Add hashtags if needed
        if metrics.hashtag_count < 2:
            refined += " #ArtificialIntelligence #Innovation"

        # Add engagement trigger if needed
        if metrics.engagement_triggers < 1:
            refined += " What are your thoughts on this?"

        # Add technical terms if needed
        if metrics.technical_terms < 2:
            tech_term = random.choice(ContentGenerator.TECH_TERMS["ai"])
            refined += f" Especially in {tech_term} applications."

        # Trim if too long
        if metrics.word_count > 50:
            words = refined.split()
            refined = " ".join(words[:50])

        return refined


# -----------------------------------------------------------------------------
# Agent Prompt
# -----------------------------------------------------------------------------

AGENT_PROMPT = """<purpose>
    You are a world-class social media strategist and content creator.
    Your goal is to generate and refine social media posts from ideas until they achieve optimal engagement potential.
</purpose>

<instructions>
    <instruction>Use the provided tools to create, analyze, and refine posts:</instruction>
    <instruction>1. Start by generating an initial post using generate_post</instruction>
    <instruction>2. Analyze the post using analyze_post to identify areas for improvement</instruction>
    <instruction>3. Refine the post using refine_post based on the analysis</instruction>
    <instruction>4. Repeat steps 2-3 until the post meets optimal criteria</instruction>
    <instruction>Include detailed reasoning with every tool call</instruction>
</instructions>

<context>
    Idea: {{idea}}
    Desired Tone: {{tone}}
    Target Audience: {{target_audience}}
</context>
"""

# -----------------------------------------------------------------------------
# Tool Functions
# -----------------------------------------------------------------------------


def generate_post(reasoning: str, idea: str, tone: str, target_audience: str) -> str:
    """Generates a post based on the provided parameters."""
    console.log(f"[blue]Generate Post Tool[/blue] - Reasoning: {reasoning}")

    try:
        post = ContentGenerator.generate(idea, tone, target_audience)
        return f"Generated Post:\n{post}"
    except ValueError as e:
        return f"Error: {str(e)}"


def analyze_post(reasoning: str, post: str) -> str:
    """Analyzes the post and provides detailed metrics."""
    console.log(f"[blue]Analyze Post Tool[/blue] - Reasoning: {reasoning}")

    # Clean the post text
    clean_post = post.replace("Generated Post:\n", "").replace("Refined Post:\n", "")

    # Get metrics
    metrics = ContentAnalyzer.analyze(clean_post)

    analysis = f"""Post Analysis:
Word Count: {metrics.word_count} ({"optimal" if 15 <= metrics.word_count <= 50 else "needs adjustment"})
Hashtags: {metrics.hashtag_count} ({"sufficient" if metrics.hashtag_count >= 2 else "needs more"})
Engagement Triggers: {metrics.engagement_triggers} ({"good" if metrics.engagement_triggers >= 1 else "needs improvement"})
Technical Terms: {metrics.technical_terms} ({"good" if metrics.technical_terms >= 2 else "needs more"})
Sentiment Score: {metrics.sentiment_score:.2f} ({"good" if 0.5 <= metrics.sentiment_score <= 1.0 else "needs adjustment"})
Overall: {"Optimal" if metrics.is_optimal() else "Needs refinement"}"""

    return analysis


def refine_post(reasoning: str, post: str, analysis: str) -> str:
    """Refines the post based on analysis results."""
    console.log(f"[blue]Refine Post Tool[/blue] - Reasoning: {reasoning}")

    # Clean the post text
    clean_post = post.replace("Generated Post:\n", "").replace("Refined Post:\n", "")

    # Parse metrics from analysis
    metrics_dict = {}
    for line in analysis.split("\n")[1:]:  # Skip the "Post Analysis:" line
        if ":" in line:
            key, value = line.split(":", 1)
            metrics_dict[key.strip()] = value.strip()

    # Create metrics object
    metrics = PostMetrics(
        word_count=int(metrics_dict["Word Count"].split()[0]),
        hashtag_count=int(metrics_dict["Hashtags"].split()[0]),
        engagement_triggers=int(metrics_dict["Engagement Triggers"].split()[0]),
        technical_terms=int(metrics_dict["Technical Terms"].split()[0]),
        sentiment_score=float(metrics_dict["Sentiment Score"].split()[0]),
    )

    # Refine the post
    refined = ContentRefiner.refine(clean_post, metrics)
    return f"Refined Post:\n{refined}"


# -----------------------------------------------------------------------------
# Main Agent Loop
# -----------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced Social Media Post Generation and Refinement Agent"
    )
    parser.add_argument(
        "--idea", required=True, help="The core idea for the social media post"
    )
    parser.add_argument("--tone", required=True, help="Desired tone of the post")
    parser.add_argument("--target", required=True, help="Target audience for the post")
    parser.add_argument(
        "-c", "--compute", type=int, default=20, help="Maximum number of agent loops"
    )
    args = parser.parse_args()

    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if not ANTHROPIC_API_KEY:
        console.print(
            "[red]Error: ANTHROPIC_API_KEY environment variable is not set[/red]"
        )
        sys.exit(1)

    client = Anthropic()

    # Prepare the initial prompt
    full_prompt = AGENT_PROMPT.replace("{{idea}}", args.idea)
    full_prompt = full_prompt.replace("{{tone}}", args.tone)
    full_prompt = full_prompt.replace("{{target_audience}}", args.target)

    messages = [{"role": "user", "content": full_prompt}]
    compute_iterations = 0
    last_content = None

    while True:
        console.rule(
            f"[yellow]Agent Loop {compute_iterations + 1}/{args.compute}[/yellow]"
        )
        compute_iterations += 1

        if compute_iterations >= args.compute:
            console.print("[yellow]Reached maximum compute loops. Exiting.[/yellow]")
            break

        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=messages,
                tools=[
                    {
                        "name": "generate_post",
                        "description": "Creates an initial social media post from an idea.",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "reasoning": {"type": "string"},
                                "idea": {"type": "string"},
                                "tone": {"type": "string"},
                                "target_audience": {"type": "string"},
                            },
                            "required": [
                                "reasoning",
                                "idea",
                                "tone",
                                "target_audience",
                            ],
                        },
                    },
                    {
                        "name": "analyze_post",
                        "description": "Analyzes the post for potential improvements.",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "reasoning": {"type": "string"},
                                "post": {"type": "string"},
                            },
                            "required": ["reasoning", "post"],
                        },
                    },
                    {
                        "name": "refine_post",
                        "description": "Improves the post based on analysis.",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "reasoning": {"type": "string"},
                                "post": {"type": "string"},
                                "analysis": {"type": "string"},
                            },
                            "required": ["reasoning", "post", "analysis"],
                        },
                    },
                ],
                tool_choice={"type": "any"},
            )

            tool_calls = [
                block
                for block in response.content
                if hasattr(block, "type") and block.type == "tool_use"
            ]

            if not tool_calls:
                console.print(
                    "[yellow]No tool calls found in response. Exiting loop.[/yellow]"
                )
                break

            for tool_call in tool_calls:
                func_name = tool_call.name
                func_args = tool_call.input

                console.print(
                    f"[blue]Tool Call:[/blue] {func_name}({json.dumps(func_args)})"
                )
                messages.append({"role": "assistant", "content": response.content})

                try:
                    if func_name == "generate_post":
                        result = generate_post(
                            reasoning=func_args["reasoning"],
                            idea=func_args["idea"],
                            tone=func_args["tone"],
                            target_audience=func_args["target_audience"],
                        )
                    elif func_name == "analyze_post":
                        result = analyze_post(
                            reasoning=func_args["reasoning"],
                            post=func_args["post"],
                        )

                        # Check if post is optimal
                        if "Overall: Optimal" in result:
                            console.print(
                                "[green]Post has reached optimal quality.[/green]"
                            )
                            console.print(
                                Panel(func_args["post"], title="Final Optimized Post")
                            )
                            return

                    elif func_name == "refine_post":
                        result = refine_post(
                            reasoning=func_args["reasoning"],
                            post=func_args["post"],
                            analysis=func_args["analysis"],
                        )
                    else:
                        raise Exception(f"Unknown tool call: {func_name}")

                    console.print(
                        f"[blue]Tool Call Result:[/blue] {func_name}(...) ->\n{result}"
                    )

                    # Check for convergence
                    current_content = PostContent(result)
                    if last_content and current_content == last_content:
                        console.print(
                            "[yellow]Post has converged but may not be optimal.[/yellow]"
                        )
                        console.print(Panel(result, title="Final Post (Converged)"))
                        return

                    last_content = current_content

                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_call.id,
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

        except Exception as e:
            console.print(f"[red]Error in agent loop: {str(e)}[/red]")
            break


if __name__ == "__main__":
    main()
