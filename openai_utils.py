import os
import requests

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")

def ask_openai(prompt: str) -> str:
    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_DEPLOYMENT_NAME}/chat/completions?api-version={AZURE_API_VERSION}"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_KEY
    }

    payload = {
        "messages": [
            {"role": "system", "content": "You are an invoice or cheque parser."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "max_tokens": 500
    }
    
    try:
        print("Sending request to OpenAI...")
        response = requests.post(url, headers=headers, json=payload)
        print("Status:", response.status_code)
        print("Raw text:", response.text)

        response.raise_for_status()

        if not response.text:
            return "❌ OpenAI returned an empty response."

        try:
            result = response.json()
            print("✅ OpenAI Result:", result)

            if "choices" in result and result["choices"]:
                return result["choices"][0]["message"]["content"]
            else:
                return "❌ No choices found in OpenAI response."

        except ValueError as json_err:
            print("❌ JSON Decode Error:", json_err)
            return f"❌ Failed to parse OpenAI response: {json_err}"

    except requests.exceptions.RequestException as e:
        print("❌ OpenAI error:", e)
        return f"❌ OpenAI error: {e}"

# Add this helper function in main.py
def generate_sql_from_question(question: str, email: str) -> str:
    """Generate SQL query from user question"""
    prompt = f"""
        You are a data analyst assistant. Generate a SQL SELECT query for Supabase (PostgreSQL) that answers this question:
        "{question}"
        
        Use ONLY these tables:
        1. upload_invoice (columns: invoice_number, sellers_name, buyers_name, date, item, quantity, amount, email, id)
        2. upload_cheique (columns: payee_name, senders_name, amount, date, bank_name, account_number, email, id)
        
        Rules:
        - Always include WHERE email = '{email}' to filter by user
        - Only use SELECT queries - never INSERT/UPDATE/DELETE
        - Return just the SQL query with no explanations
        - Use proper JOINs if needed
        - Format dates properly (YYYY-MM-DD)
        - Include relevant columns based on the question
        
        Examples:
        Question: "Show my recent invoices"
        Query: SELECT invoice_number, sellers_name, date, amount FROM upload_invoice WHERE email = '{email}' ORDER BY date DESC LIMIT 5
        
        Question: "How much did I spend on groceries last month?"
        Query: SELECT SUM(amount) as total FROM upload_invoice WHERE email = '{email}' AND item ILIKE '%grocery%' AND date >= date_trunc('month', CURRENT_DATE - interval '1 month') AND date < date_trunc('month', CURRENT_DATE)
        
        Now generate SQL for this question:
        "{question}"
        """
    return ask_openai(prompt).strip()

def humanize_data_response(data: list, question: str) -> str:
    """Convert raw SQL results to human-readable response"""
    prompt = f"""
        You are a friendly financial assistant. Explain this data in simple English to answer the user's question.
        
        User's question: "{question}"
        
        Data (in JSON format):
        {json.dumps(data, indent=2)}
        
        Guidelines:
        - Be concise but helpful
        - Highlight key numbers/trends
        - Use natural language
        - Don't mention SQL or database terms
        - Format amounts/numbers properly
        - If no data found, suggest possible reasons
        
        Provide only the response text, no prefixes or explanations.
        """
    return ask_openai(prompt).strip()


