import asyncio
import json
import os
import argparse
from playwright.async_api import async_playwright
from openai import OpenAI, APIError

# LLM Configuration
# Read API key from environment variable
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
openai_client = OpenAI(api_key=api_key)
model = "gpt-4.1-nano"

# Example prompt format
def generate_prompt(field_info, mock_data):
    """Generates a prompt for the LLM to find the correct value for a form field."""
    return f"""
Given this form field:
- Label: {field_info.get('label')}
- Name attribute: {field_info.get('name')}
- Placeholder: {field_info.get('placeholder')}

Choose the correct value from this mock data:
{json.dumps(mock_data, indent=2)}

Respond ONLY with the matching value. If none applies, respond with "SKIP".
"""

async def extract_fields(page):
    """Extracts input, select, and textarea fields from the page, along with their labels."""
    fields = []
    inputs = await page.query_selector_all("input, select, textarea")

    for input_elem in inputs:
        name = await input_elem.get_attribute("name")
        placeholder = await input_elem.get_attribute("placeholder")
        input_id = await input_elem.get_attribute("id")
        label_text = ""

        if input_id:
            label = await page.query_selector(f"label[for='{input_id}']")
            if label:
                label_text = await label.inner_text()

        fields.append({
            "element": input_elem,
            "name": name,
            "placeholder": placeholder,
            "label": label_text.strip() if label_text else None
        })

    return fields

async def fill_fields(fields, page, mock_data):
    """Iterates through extracted fields, uses LLM to find the value, and fills the form."""
    for field in fields:
        prompt = generate_prompt(field, mock_data)
        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            value = response.choices[0].message.content.strip()

            if value != "SKIP":
                tag_name = await field["element"].evaluate("(el) => el.tagName")
                tag_name = tag_name.lower()

                if tag_name == "input":
                    input_type = await field["element"].get_attribute("type")
                    if input_type in ["text", "email", "tel", "number"]:
                        await field["element"].fill(value)
                    elif input_type == "checkbox" and value.lower() in ["yes", "true"]:
                        await field["element"].check()
                    elif input_type == "radio":
                        # Assuming value matches the specific radio button's value attr;
                        # might need adjustment if LLM returns label text instead.
                        # Find the specific radio button with the matching value if multiple share the name.
                        radio_to_select = await page.query_selector(f"input[type='radio'][name='{field['name']}'][value='{value}']")
                        if radio_to_select:
                            await radio_to_select.check()
                        else:
                            print(f"⚠️ Could not find radio button with name '{field['name']}' and value '{value}'")
                elif tag_name == "textarea":
                    await field["element"].fill(value)
                elif tag_name == "select":
                    try:
                        # Attempt to select by label first, as LLM likely returns visible text
                        await field["element"].select_option(label=value)
                    except Exception as e:
                        # Broad exception catch: Playwright might raise different errors
                        # if the option doesn't exist or isn't interactable.
                        # Could refine to catch specific exceptions like TimeoutError.
                        print(f"ℹ️ Could not select option '{value}' for select field '{field.get('name', 'N/A')}': {e}")
                        # Optionally, try selecting by value attribute if label fails
                        try:
                            await field["element"].select_option(value=value)
                        except Exception as e2:
                            print(f"ℹ️ Could not select option by value '{value}' either: {e2}")

        except APIError as e:
            print(f"❌ OpenAI API error for field '{field.get('name', 'N/A')}': {e}")
            # Decide how to proceed: skip field, retry, halt script?
            continue # Skip this field on API error
        except Exception as e:
            print(f"❌ An unexpected error occurred for field '{field.get('name', 'N/A')}': {e}")
            continue # Skip this field

async def main():
    """Main function to run the playwright automation."""

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Automated form filler using Playwright and OpenAI.")
    parser.add_argument("--url", required=True, help="The URL of the web form to fill.")
    parser.add_argument("--data-file", required=True, help="Path to the JSON file containing mock data.")
    args = parser.parse_args()

    # --- Load Mock Data ---   
    try:
        with open(args.data_file, 'r') as f:
            mock_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Mock data file not found at '{args.data_file}'")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from '{args.data_file}'. Please ensure it's valid JSON.")
        return
    except Exception as e:
        print(f"❌ An unexpected error occurred while loading mock data: {e}")
        return

    # --- Playwright Automation ---
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            record_video_dir="videos/",
            # viewport={ 'width': 1280, 'height': 720 }
        )
        page = await context.new_page()
        try:
            print(f"Navigating to {args.url}...")
            await page.goto(args.url) # Use URL from argument

            print("Extracting form fields...")
            fields = await extract_fields(page)
            print(f"Found {len(fields)} fields. Attempting to fill...")

            # Pass loaded mock_data to fill_fields
            await fill_fields(fields, page, mock_data) 

            print("✅ Form filling complete (excluding signature and submission).")

        except Exception as e:
            print(f"❌ An error occurred during Playwright operations: {e}")
        finally:
            print("Closing browser and saving video...")
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
