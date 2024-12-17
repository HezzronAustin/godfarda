#!/usr/bin/env python3

"""
Management script for AI Tools Ecosystem services.
"""

import click
import subprocess
import sys
import os

@click.group()
def cli():
    """Management CLI for AI Tools Ecosystem services."""
    pass

@cli.command()
def telegram():
    """Start the Telegram bot service."""
    click.echo("Starting Telegram bot...")
    try:
        subprocess.run([
            "python3", "-m", 
            "src.tools.communication.telegram.bot"
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
    except KeyboardInterrupt:
        click.echo("\nTelegram bot stopped")

@cli.command()
@click.option('--host', default="127.0.0.1", help="Host to bind to")
@click.option('--port', default=8000, help="Port to bind to")
def dashboard(host, port):
    """Start the dashboard service."""
    click.echo(f"Starting dashboard on {host}:{port}...")
    try:
        subprocess.run([
            "python3", "-m", "uvicorn",
            f"src.api.dashboard.server:app",
            f"--host={host}",
            f"--port={port}",
            "--reload"
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
    except KeyboardInterrupt:
        click.echo("\nDashboard stopped")

@cli.command()
def ollama():
    """Start the Ollama server."""
    click.echo("Starting Ollama server...")
    try:
        subprocess.run(["ollama", "serve"])
    except KeyboardInterrupt:
        click.echo("\nOllama server stopped")

if __name__ == '__main__':
    cli()
