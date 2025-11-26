#!/bin/bash

# Quick start script for the Rehearsed Multi-Student backend

echo "🚀 Starting Rehearsed Multi-Student API..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env and add your GOOGLE_API_KEY"
    echo ""
    exit 1
fi

# Check if virtual environment exists
if [ ! -d .venv ]; then
    echo "📦 Installing dependencies..."
    poetry install
    echo ""
fi

# Start the server
echo "✨ Starting API server on http://localhost:8000"
echo "📚 API docs will be at http://localhost:8000/docs"
echo ""

poetry run uvicorn rehearsed_multi_student.api.main:app --reload
