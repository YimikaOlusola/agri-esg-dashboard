from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import streamlit as st
import os

@st.cache_data(ttl=3600)  # Cache for 1 hour
def generate_ai_insights(
    esg_score: float,
    e_score: float,
    s_score: float,
    emissions_per_ha: float,
    emissions_per_tonne: float,
    yield_per_ha: float,
    female_share: float,
    accidents: float,
    farm_id: str,
    farmer_name: str = None
) -> list[str]:
    """
    Generate AI-powered, farmer-friendly insights using Gemini.
    Returns list of 3-4 actionable recommendations.
    """
    
    # Check if API key exists
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        greeting = f"Hello {farmer_name}!" if farmer_name else "Hello!"
        return [
            f"{greeting} Set up your Google API key to get personalized advice.",
            "Check your .env file for GOOGLE_API_KEY configuration."
        ]
    
    # Get greeting name (Default to 'Friend' if None)
    greeting_name = farmer_name if farmer_name and str(farmer_name).lower() != 'nan' else "Friend"
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a helpful farming advisor speaking to a farmer named {greeting_name}.

Rules:
- ALWAYS start your response with a standalone greeting line: "Hello {greeting_name}!"
- Then provide 3-4 simple, actionable tips
- Use SIMPLE words (like you're talking to a 12-year-old)
- NO technical jargon
- Use actual numbers from their farm data where possible
- Address them as "you"

Example Output Format:
Hello {greeting_name}!
Try using 10 bags less fertilizer next month to save money.
Consider hiring 2 more women for the harvest season.
Great safety record! Keep it up.
"""),
        
        ("user", """Farm Data:
- Overall Score: {esg_score}/100
- Environment Score: {e_score}/100 
- Social Score: {s_score}/100
- Pollution: {emissions} kg/ha
- Accidents: {accidents}

Give me my personal advice list.""")
    ])
    
    try:
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            temperature=0.7,
            google_api_key=api_key
        )
        
        # Create chain
        chain = prompt | llm
        
        # Invoke
        response = chain.invoke({
            "esg_score": round(esg_score, 0),
            "e_score": round(e_score, 0),
            "s_score": round(s_score, 0),
            "emissions": round(emissions_per_ha, 1),
            "accidents": round(accidents, 1)
        })
        
        # Parse response into list
        content = response.content.strip()
        
        insights = []
        for line in content.split('\n'):
            line = line.strip()
            clean_line = line.lstrip('•-*123456789. ')
            
            is_greeting = clean_line.lower().startswith(('hello', 'hi ', 'dear', 'greetings'))
            
            if clean_line and (len(clean_line) > 10 or is_greeting):
                insights.append(clean_line)
        
        if insights:
            return insights[:4]
        else:
            return [f"Hello {greeting_name}! I couldn't generate specific tips right now."]
    
    except Exception as e:
        return [
            f"Hello {greeting_name}!",
            f"System is busy. Your score is {round(esg_score, 0)}/100.",
            "Please try refreshing the page."
        ]