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
    farm_id: str
) -> list[str]:
    """
    Generate AI-powered, farmer-friendly insights using Gemini.
    Returns list of 3-4 actionable recommendations.
    """
    
    # Check if API key exists
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return [
            "Set up your Google API key to get personalized advice.",
            "Check your .env file for GOOGLE_API_KEY configuration.",
            "Contact support for help with AI features."
        ]
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful farming advisor speaking to farmers with basic education.

Rules:
- Use SIMPLE words (like you're talking to a 12-year-old)
- NO technical jargon or abbreviations
- Give 3-4 specific, actionable tips they can do THIS SEASON
- Be encouraging and positive
- Use actual numbers from their farm data
- Focus on practical steps, not theory
- Each tip should be 1-2 short sentences

Examples of GOOD advice:
✓ "Your fertilizer use is high. Try using 10 bags less next month - you'll save money and help the soil."
✓ "Great safety record! Keep having your morning team meetings."
✓ "Farms with more women workers earn 15% more. Consider hiring 2-3 more women for harvest season."

Examples of BAD advice:
✗ "Optimize your nitrogen input to reduce your carbon footprint"
✗ "Implement ESG best practices"
✗ "Your emissions per tonne are suboptimal"
"""),
        
        ("user", """Farm Data:
- Overall Score: {esg_score}/100
- Environment Score: {e_score}/100 (pollution, fertilizer, water)
- Social Score: {s_score}/100 (workers, safety)
- Pollution: {emissions} kg per hectare
- Crop Yield: {yield_val} tonnes per hectare  
- Women Workers: {female_pct}%
- Accidents: {accidents} per 100 workers

Give me 3-4 simple actions to improve my farm this season.""")
    ])
    
    try:
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
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
            "yield_val": round(yield_per_ha, 1),
            "female_pct": round(female_share * 100, 0),
            "accidents": round(accidents, 1)
        })
        
        # Parse response into list
        content = response.content.strip()
        
        # Split by common delimiters
        insights = []
        for line in content.split('\n'):
            line = line.strip()
            # Remove bullet points, numbers, etc.
            line = line.lstrip('•-*123456789. ')
            if line and len(line) > 20:  # Filter out empty or too-short lines
                insights.append(line)
        
        # Return first 3-4 insights
        return insights[:4] if insights else ["Unable to generate insights. Please try again."]
    
    except Exception as e:
        # Fallback insights if AI fails
        return [
            f"⚠️ AI service temporarily unavailable.",
            f"Your overall score is {round(esg_score, 0)}/100.",
            "Try uploading your data again or contact support."
        ]
