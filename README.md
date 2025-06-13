# Baby Alpha: AI-Driven Document Improver & Novel Idea Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Baby Alpha is a simple yet powerful Python-based AI agent designed to iteratively refine research papers (or any text document) and brainstorm novel solutions to complex problems using local Large Language Models (LLMs) via Ollama.**

The original vision was to have agentic LLMs be able to have their own chat room and social network where they could use millions of decentralised computers around the world to work on problems (crowd sourcing compute). The project took five months (started Jan 15 2025) of work using ChatGPT o3-mini before moving to Google Studio to try to fix it. In deciding to do a test and eliminate complexity, a basic non-modular version was created for refining the prompt loop. This led to a much more effective version for iterating improvments. Soon after, Google announced AlphaEvolve. Panic struct but AlphaEvolve was different. It worked on math and code. Baby Alpha works on research paper ideas. Phew!!!

It works by engaging in a structured, multi-step "thought process" to:
1.  Critically analyze a document by listing its Pros and Cons.
2.  Select the most critical "Con" (problem) to address.
3.  Decide whether a direct fix or in-depth brainstorming is more appropriate for the chosen problem.
4.  If brainstorming:
    *   Explore past analogies (methods from the past that are analagous to the subject of the "Con").
    *   Explore unrelated cross-disciplinary fields.
    *   Explore "left-field" unconventional ideas.
    *   Systematically combine these brainstormed elements to spark novel connections (Code cracking all 27 combinations).
    *   Distill the most promising novel ideas from these combinations.
5.  Synthesize all gathered information (original document + identified problem + direct fix attempt OR all brainstorming notes) into a new, improved version of the document, aiming for a comprehensive, detailed, and thorough output.
6.  Evaluate if the new version is an improvement.
7.  Repeat the cycle, continuously evolving the document.

The goal is to create a foundational tool that can autonomously explore topics, generate unique insights, and build upon its work over many iterations, potentially leading to breakthroughs that a human or a single-prompt LLM interaction might miss. Someone could use the same prompts with a standard LLM but the iterations would be significantly slower. Many people use these same prompts with standard LLMs without even knowing realising it.

## Key Features

*   **Iterative Improvement:** Continuously refines a document over multiple cycles.
*   **Structured Problem Solving:** Uses a "Pros/Cons" approach to identify areas for improvement.
*   **Conditional Brainstorming:** Intelligently decides whether to attempt a direct fix or engage in deeper, multi-faceted brainstorming for novel solutions.
*   **Combinatorial Innovation:** Forces the LLM to explore unique combinations of ideas from diverse sources.
*   **Local LLM Powered:** Utilizes Ollama to run powerful language models locally on your machine.
*   **Configurable:** Easily adjust parameters like the LLM model, temperatures for different tasks, and iteration count via `simple_config.json`.
*   **Simple Code:** Easily alter the prompts and loop structure to create numerous different processes for different outcomes.
*   **Open Source:** MIT Licensed, ready for community exploration and enhancement!

## How It Works


![Baby Alpha Flowchart](https://i.imgur.com/tf8gMgc.jpeg)

Briefly, Baby Alpha takes an initial document and iteratively refines it by:
1.  Identifying a "Con" (problem).
2.  Choosing a strategy: "Direct Fix" or "Brainstorm".
3.  If "Brainstorm", it generates diverse ideas and combinations.
4.  All findings (direct fix content or brainstormed insights) are compiled as "notes".
5.  It then synthesizes a new version of the entire document by integrating these notes into the original content from the start of the iteration, focusing on addressing the identified problem.
6.  This new version is evaluated against the previous one. If deemed an improvement (not a degradation), it becomes the new baseline for the next iteration.

## Getting Started

### Prerequisites

1.  **Python:** Ensure you have Python 3.10 or newer installed (may work on ealier versions such as 3.8 but hasn't been tested).
2.  **Git:** To clone a respository, you require git to be installed. [Git install](https://github.com/git-guides/install-git)
2.  **Ollama:** You MUST have Ollama installed and running. I recomend the windows app. This is so that the Install.bat can pull the models.
    *   **Windows Users:** Download and install the [Ollama Windows app](https://ollama.com/download/windows). **Ensure the Ollama application is running BEFORE proceeding with the `Install.bat` script.**
    *   **Linux/macOS Users:** Follow the instructions at [ollama.com](https://ollama.com/). Ensure the Ollama server is running (`ollama serve` if not running as a service).

### Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Steven-Hammon/baby-alpha.git
    cd baby-alpha
    ```
2.  **Windows Users:**
    *   Simply double-click `Install.bat`. This script will:
        *   Attempt to create a Python virtual environment (`venv`).
        *   Install required Python packages (`ollama` `ChromaDB`). *note ChromaDB is RAG capabilities (memory) but not in this early version of Baby Alpha.
        *   Instruct Ollama (if running) to pull the recommended LLM models.
3.  **Linux/macOS Users (Manual Setup):**
    *   Open your terminal in the `baby-alpha` directory.
    *   Create and activate a virtual environment (recommended):
        ```bash
        python3 -m venv venv
        source venv/bin/activate  # On Linux/macOS
        # For Windows PowerShell in venv: .\venv\Scripts\Activate.ps1
        ```
    *   Install requirements:
        ```bash
        pip install -r requirements.txt
        ```
    *   Pull Ollama Models (ensure Ollama server is running):
        ```bash
        ollama pull gemma3:12b-it-qat  # Default recommended model (requires ~16-20GB VRAM)
        ollama pull gemma3:4b         # Alternative for lower VRAM (e.g., 8GB)
        ```

### Ollama VRAM Configuration (Optional, for Windows Users with GPUs)

If you have a dedicated GPU and want to manage how Ollama uses its VRAM (to prevent it from using all available memory and to allow offloading to CPU RAM if VRAM is full), you can use the provided `.bat` scripts in the `Ollama_VRAM_Config_Scripts` directory.

*   `set_ollama_vram_7gb.bat`
*   `set_ollama_vram_11gb.bat`
*   `set_ollama_vram_15gb.bat`
*   `set_ollama_vram_19gb.bat`
*   `set_ollama_vram_23gb.bat`
*   `set_ollama_vram_defaults.bat` (to remove the VRAM limit setting)

Run the script that best matches your GPU's VRAM capacity **before** starting the Ollama application for the setting to take effect for that session, or set it system-wide as per the script's output. These scripts set the `OLLAMA_MAX_VRAM` environment variable.

### Configuration (`simple_config.json`)

Before running, review and edit `simple_config.json`:

*   `"document_title"`: The title of the research paper Baby Alpha will work on. This is used in prompts to keep the LLM focused (about 3 sentences long).
*   `"document_path"`: The filename for the main document (e.g., `"project_document.txt"`).
*   `"gen_model"`: The Ollama model to use.
    *   Default: `"gemma3:12b-it-qat"` (powerful, slower, needs more VRAM)
    *   Alternative: `"gemma3:4b"` (less powerful, faster, runs on ~8GB VRAM)
*   `"max_iterations_simple"`: How many improvement cycles to run (e.g., 100).
*   `"temperature_..."`: Values from 0.0 (deterministic) to ~1.0+ (more creative/random).
    *   `temperature_general`: For decision-making.
    *   `temperature_brainstorm_min`/`max`: Random Range for brainstorming new ideas.
    *   `temperature_synthesis`: For writing/rewriting the document.
*   `"max_backup_files"`: How many previous versioned backups of the document to keep.
*   `"max_convo_log_size_mb"`: Approximate size in MB before `convo_simple.txt` is rotated.
*   `"number_pred_simple"` / `"number_ctx_simple"`: Max prediction tokens and context window for LLM calls. Adjust based on your model and system capabilities.

### Initial Document (`project_document.txt`)

*   Place your starting document content in the file specified by `document_path` (default: `project_document.txt`).
*   If the file doesn't exist, Baby Alpha will create a default seed document based on the `document_title` (which, by default, guides it to write about itself!).

## Running Baby Alpha

1.  **Ensure Ollama is running** with the desired model available.
2.  **Windows Users:** Double-click `Start.bat`.
3.  **Linux/macOS Users:**
    *   Activate your virtual environment (`source venv/bin/activate`).
    *   Run: `python simple_document_improver.py`

The script will start the iterative process. You will see output in your console and detailed logs being written to the `logs/` directory.

## Understanding the Output

*   **`project_document.txt`**: This file is overwritten at the end of each successful iteration where the LLM deems the new version an improvement. This is your evolving research paper! You can open the current version in notepad to look at where it's up to while Baby Alpha overwrites the stored file.
*   **`document_backups/`**: Contains versioned backups (e.g., `project_document_v1.txt`, `project_document_v2.txt`) created each time the main document is successfully updated.
*   **`logs/simple_improver.log`**: The main operational log for Baby Alpha. Shows the steps, decisions, and errors.
*   **`logs/convo_simple.txt`**: A detailed transcript of all prompts sent to the LLM and its raw responses. Very useful for debugging prompts and understanding the AI's "reasoning."

## Customization & Experimentation

This "simple improver" script is designed to be a foundation. You are encouraged to:

*   **Modify Prompts:**The core logic is in `simple_document_improver.py`. Experiment with different phrasings for the problem identification, brainstorming, synthesis, and evaluation prompts. Advanced prompt engineering knowledge needed.
*   **Change `DOCUMENT_TITLE` and initial `project_document.txt`:** Explore different research topics!
     *   *Example Title 1 (Psychology):* "The Cognitive Dissonance of AI: Exploring Human Psychological Responses to Near-Human Intelligence"
     *   *Example Title 2 (ASI Governance):* "Decentralized Autonomous Organizations (DAOs) as a Framework for Verifiable and Ethical ASI Control"
     *   *Example Title 3 (Space Exploration):* "Novel Propulsion Systems for Interstellar Travel: A White Paper on Theoretical Breakthroughs Beyond Conventional Physics"
     *   *Example Title 4 (Sustainable Energy):* "Bio-Integrated Photovoltaics: A Self-Replicating, Organic Approach to Global Sustainable Energy"
*   **Adjust Temperatures:** See how different creativity levels affect the output.
*   **Try Different LLM Models:** Experiment with other models available through Ollama.

## Roadmap & Future Ideas (Call to the Community!)

Baby Alpha (Simple Improver) is just the beginning! The original vision is a more complex, modular multi-agent system. I have heaps on the following worked out already however I don't have the time to create it all. I have other projects that are more important. I'm happy to discuss them with anyone. I'll be on the discord channel a lot. Here are some directions this project (or new ones inspired by it) could take:

1.  **Modularize Baby Alpha:** Convert this script's logic into the multi-process, piped architecture (Hub, LLM module, etc.) for greater scalability and the ability to add new specialized modules.
2.  **Tool Usage:** Integrate capabilities for the agent to use external tools (web search, code execution, file system access – with extreme caution and safety measures!).
3.  **Vision Module:** Allow the agent to "see" screen content or images and incorporate that into its brainstorming and document generation.
4.  **Automated Prompt Engineering:** Can Baby Alpha learn to refine its OWN prompts over time to get better results?
5.  **Prompting an LLM to create prompts (from a file of weighted prompts) to send to the other LLM.
5.  **AlphaEvolve Emulation:** Design prompt chains specifically to mimic the problem-solving and code-generation strategies of systems like AlphaEvolve. Could we improve AlphaEvolve?
6.  **AI Agent Chatroom:** Develop the networking components for multiple Baby Alpha agents (or other AI agents) to connect, share information, and brainstorm *together*.
7.  **Specialized Brainstorming Modules:** Create modules that are experts in specific types of creative thinking (e.g., a TRIZ module, a Six Thinking Hats module).
8.  **Fact-Checking & Verification Loop:** Integrate a step where the LLM's generated content is cross-referenced against known facts or reliable sources.
9.  **Ethical Guardrail Module:** A dedicated module that reviews generated content for ethical alignment based on predefined principles.
10. **User Interface (GUI):** Build a more interactive GUI for managing Baby Alpha, reviewing changes, and guiding its process.

If any of these ideas excite you, fork the repo, start a discussion, or join the community!

## Community & Support

*   **Join our Discord channels:** - Let's discuss ideas, share results, and build together! https://discord.gg/m5vyz8TrgT
*   **GitHub Issues:** Report bugs or suggest features via the Issues tab.

## Contributing

Reach out to the community and pitch your idea. See if others are willing to help you and you help them. Make sure there is a clear leader and owner of the project direction, for the final say. But also be open and willing to incorporate anything that others might envision. It's okay to create 2 different versions of things. Feel free to ask for assistance in the discussions. Members will be more than happy to help if they aren't busy.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
