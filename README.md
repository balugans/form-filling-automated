# Automated Form Filler using Playwright and OpenAI

This project demonstrates an automated web agent that navigates to a specified URL, extracts form fields, and uses an OpenAI language model (LLM) to intelligently fill out the form based on provided mock data.

## Acknowledgements

There was use of coding agents including Cursor to finish the project on time and polish the README. 

## Features

*   Navigates to a target web form URL.
*   Extracts input fields, text areas, and select dropdowns along with their labels.
*   Uses an OpenAI model (`gpt-4o-mini` or configurable) to determine the appropriate value for each field based on mock data.
*   Handles text inputs, emails, numbers, checkboxes, radio buttons, and select dropdowns (attempts selection by label and falls back to value).
*   Records a video of the browser session to a `videos/` directory.
*   Includes basic error handling for API calls and form interactions.

## Setup

1.  **Clone the repository (if applicable):**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install Dependencies:**
    Ensure you have Python 3.7+ and `uv` (or `pip`) installed. Install the required packages:
    ```bash
    uv pip install -r requirements.txt
    ```
    Or using pip:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright Browsers:**
    Download the necessary browser binaries for Playwright:
    ```bash
    playwright install
    ```

4.  **Set OpenAI API Key:**
    You need an API key from OpenAI. Set it as an environment variable named `OPENAI_API_KEY` in your terminal session.

    *   **PowerShell (Windows):**
        ```powershell
        $env:OPENAI_API_KEY = "your_openai_api_key"
        ```
    *   **Command Prompt (Windows):**
        ```cmd
        set OPENAI_API_KEY=your_openai_api_key
        ```
    *   **Bash/Zsh (Linux/macOS):**
        ```bash
        export OPENAI_API_KEY="your_openai_api_key"
        ```
    Replace `"your_openai_api_key"` with your actual key. **Do not commit your API key to version control.**

## Running the Script

Execute the main script from your terminal, providing the target URL and the path to your mock data JSON file:

```bash
python main.py --url <target-form-url> --data-file <path-to-your-data.json>
```

**Example:**
```bash
python main.py --url https://mendrika-alma.github.io/form-submission/ --data-file mockup_data.json
```

The script will:
*   Parse the command-line arguments.
*   Load the mock data from the specified JSON file.
*   Launch a Chromium browser window.
*   Navigate to the specified URL.
*   Attempt to fill the form fields using the loaded data and the LLM.
*   Print status messages to the console.
*   Save a `.webm` video recording of the session in the `videos/` directory upon completion.

## Configuration

*   **Target URL:** Provided via the `--url` command-line argument (required).
*   **Mock Data:** The path to the JSON file containing data for filling the form is provided via the `--data-file` command-line argument (required). See `mockup_data.json` for an example structure.
*   **LLM Model:** The OpenAI model used can be changed by modifying the `model` variable in `main.py`. 