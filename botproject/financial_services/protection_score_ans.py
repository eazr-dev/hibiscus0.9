import json
import os
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import dotenv

# Import LLM manager with fallback system
try:
    from ai_chat_components.llm_config import get_llm
    # Get LLM with automatic fallback (tries GPT-3.5 first, then GLM)
    llm = get_llm(use_case='protection_score')
except ImportError:
    # Fallback to direct initialization if llm_config not available
    llm = ChatOpenAI(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-3.5-turbo",
        temperature=0.5
    )

def answer_protection_score_question(user_question: str, user_data_json: str) -> str:
    """
    Answer user questions about their protection score using their policy data
    
    Args:
        user_question: The question user is asking (e.g., "what is my protection score")
        user_data_json: JSON string containing user's policy analysis data
        
    Returns:
        str: AI-generated answer based on the user's data
    """
    try:
        # Parse the JSON data
        user_data = json.loads(user_data_json) if isinstance(user_data_json, str) else user_data_json
        
        # Extract the first analysis (latest one)
        if isinstance(user_data, list) and len(user_data) > 0:
            analysis = user_data[0]
        elif isinstance(user_data, dict):
            analysis = user_data
        else:
            return "I couldn't find your policy data. Please upload your insurance policy first."
        
        analysis_data = analysis.get("analysis_data", {})
        
        # Create a comprehensive prompt for the LLM
        prompt = f"""
You are an insurance expert assistant. Answer the user's question about their insurance policy based on the provided data.

User Question: "{user_question}"

User's Insurance Policy Data:
- Insurance Type: {analysis_data.get('insurance_type', 'N/A')}
- Total Protection Score: {analysis_data.get('total_score', 'N/A')}/100
- Protection Level: {analysis_data.get('protection_level', 'N/A')}
- General Recommendation: {analysis_data.get('general_recommendation', 'N/A')}
- Extraction Confidence: {analysis_data.get('extraction_confidence', 'N/A')}%

Category Scores:
{json.dumps(analysis_data.get('category_scores', {}), indent=2)}

Policy Information:
{json.dumps(analysis_data.get('policy_info', {}), indent=2)}

User Information:
{json.dumps(analysis_data.get('user_info', {}), indent=2)}

Personalized Recommendations:
{json.dumps(analysis_data.get('personalized_recommendations', []), indent=2)}

File Information:
- Uploaded File: {analysis.get('uploaded_filename', 'N/A')}
- Analysis Date: {analysis.get('created_at', 'N/A')}

Instructions:
1. Answer the user's question directly and specifically based on their data
2. Use a conversational, helpful tone
3. If asking about protection score, provide the exact score and explain what it means
4. If asking about recommendations, list them clearly with priorities
5. If asking about policy details, extract relevant information from the policy_info section
6. If asking about personal information, use data from user_info section
7. Include relevant context and actionable advice when appropriate
8. Keep the response concise but informative
9. If the question cannot be answered from the provided data, say so clearly

Answer the user's question now:
"""

        # Send to LLM
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        
        return response.content.strip()
        
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON data provided. Please check the data format."
    except Exception as e:
        return f"Error: I encountered an issue while processing your question: {str(e)}"